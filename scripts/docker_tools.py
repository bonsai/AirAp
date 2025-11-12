"""
統合Dockerツール: ビルド、タグ付け、プッシュ、対話的操作を一つのスクリプトで提供
"""
import os
import sys
import subprocess
import time
import yaml
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from loguru import logger

# 設定を読み込む
def load_config(config_path: str = None) -> Dict[str, Any]:
    """設定ファイルを読み込む"""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # テンプレート変数を解決
        config_str = yaml.dump(config)
        config_str = config_str.replace(
            '{{ docker_hub.username }}', 
            config['docker_hub'].get('username', '')
        )
        config_str = config_str.replace(
            '{{ docker_hub.repository }}', 
            config['docker_hub'].get('repository', '')
        )
        config_str = config_str.replace(
            '{{ docker_hub.full_name }}', 
            f"{config['docker_hub'].get('username', '')}/{config['docker_hub'].get('repository', '')}"
        )
        
        config = yaml.safe_load(config_str)
        return config
    except Exception as e:
        logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

# グローバル設定
CONFIG = load_config()

# ログ設定
logger.remove()
logger.add(
    CONFIG.get('logging', {}).get('file', 'build.log'),
    rotation=CONFIG.get('logging', {}).get('rotation', '10 MB'),
    level=CONFIG.get('logging', {}).get('level', 'INFO'),
    encoding='utf-8'
)
logger.add(sys.stderr, level=CONFIG.get('logging', {}).get('level', 'INFO'))

def run_command(cmd: List[str], check: bool = True, show_progress: bool = False) -> Tuple[int, str, str]:
    """コマンドを実行する"""
    logger.info(f"実行中: {' '.join(cmd)}")
    
    try:
        if show_progress:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            stdout_lines = []
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    print(line, flush=True)
                    stdout_lines.append(line)
                    logger.debug(line)
            
            process.wait()
            stdout = '\n'.join(stdout_lines)
            stderr = ""
            returncode = process.returncode
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                logger.info(result.stdout)
            if result.stderr:
                logger.warning(result.stderr)
            return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"コマンドが失敗しました: {e}")
        logger.error(f"stderr: {e.stderr}")
        if check:
            raise
        return e.returncode, e.stdout, e.stderr

def check_docker_installed() -> bool:
    """Dockerがインストールされているか確認"""
    try:
        run_command(["docker", "--version"], check=False)
        return True
    except FileNotFoundError:
        logger.error("Dockerがインストールされていません。")
        return False

def check_docker_login() -> bool:
    """Docker Hubにログインしているか確認"""
    try:
        run_command(["docker", "info"], check=True)
        return True
    except subprocess.CalledProcessError:
        logger.error("Dockerにログインしていません。`docker login`を実行してください。")
        return False

def build_image(
    dockerfile: Optional[str] = None,
    image_name: Optional[str] = None,
    tag: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None
) -> bool:
    """Dockerイメージをビルド"""
    if dockerfile is None:
        dockerfile = CONFIG['defaults'].get('dockerfile')
    if image_name is None:
        image_name = CONFIG['defaults'].get('image_name')
    if tag is None:
        tag = CONFIG['defaults'].get('tag')
    
    if not os.path.exists(dockerfile):
        logger.error(f"Dockerfileが見つかりません: {dockerfile}")
        return False
    
    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", f"{image_name}:{tag}",
        "."
    ]
    
    if build_args:
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])
    
    try:
        run_command(cmd, show_progress=True)
        logger.success(f"イメージのビルドが完了しました: {image_name}:{tag}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"イメージのビルドに失敗しました: {e}")
        return False

def tag_image(
    source_image: str,
    target_image: str,
    source_tag: str = "latest",
    target_tag: Optional[str] = None
) -> bool:
    """Dockerイメージにタグを付ける"""
    if target_tag is None:
        target_tag = source_tag
    
    source = f"{source_image}:{source_tag}"
    target = f"{target_image}:{target_tag}"
    
    try:
        run_command(["docker", "tag", source, target])
        logger.success(f"タグを設定しました: {source} -> {target}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"タグの設定に失敗しました: {e}")
        return False

def push_image(
    image_name: str,
    tag: str = "latest",
    username: Optional[str] = None
) -> bool:
    """Docker Hubにイメージをプッシュ"""
    if username:
        full_image_name = f"{username}/{image_name}"
    else:
        full_image_name = f"{CONFIG['docker_hub']['username']}/{image_name}"
    
    # タグ付け
    source = f"{image_name}:{tag}"
    target = f"{full_image_name}:{tag}"
    
    if not tag_image(image_name, full_image_name, tag, tag):
        return False
    
    try:
        run_command(["docker", "push", target], show_progress=True)
        logger.success(f"イメージをプッシュしました: {target}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"イメージのプッシュに失敗しました: {e}")
        return False

def build_and_push(
    dockerfile: Optional[str] = None,
    image_name: Optional[str] = None,
    tag: Optional[str] = None,
    username: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None,
    skip_build: bool = False,
    skip_push: bool = False
) -> bool:
    """ビルドとプッシュを一括実行"""
    if not check_docker_installed():
        return False
    
    if not skip_build and not build_image(dockerfile, image_name, tag, build_args):
        return False
    
    if not skip_push and not push_image(
        image_name or CONFIG['defaults'].get('image_name'),
        tag or CONFIG['defaults'].get('tag'),
        username or CONFIG['docker_hub'].get('username')
    ):
        return False
    
    return True

def get_input(prompt: str, default: str = None) -> str:
    """ユーザーからの入力を取得"""
    if default:
        return input(f"{prompt} (デフォルト: {default}): ") or default
    return input(f"{prompt}: ")

def confirm(prompt: str) -> bool:
    """ユーザーに確認を求める"""
    while True:
        response = input(f"{prompt} [y/N]: ").lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no", ""]:
            return False
        print("y または n を入力してください。")

def show_settings():
    """現在の設定を表示"""
    print("\n=== 現在の設定 ===")
    print(f"Docker Hubユーザー: {CONFIG['docker_hub']['username']}")
    print(f"リポジトリ: {CONFIG['docker_hub']['repository']}")
    print(f"デフォルトDockerfile: {CONFIG['defaults']['dockerfile']}")
    print(f"デフォルトイメージ名: {CONFIG['defaults']['image_name']}")
    print(f"デフォルトタグ: {CONFIG['defaults']['tag']}")
    print("=================\n")

def menu_build_only():
    """ビルドのみを実行"""
    print("\n=== ビルドのみを実行 ===")
    dockerfile = get_input("Dockerfileのパス", CONFIG['defaults']['dockerfile'])
    image_name = get_input("イメージ名", CONFIG['defaults']['image_name'])
    tag = get_input("タグ", CONFIG['defaults']['tag'])
    
    if confirm(f"{image_name}:{tag} をビルドしますか？"):
        build_image(dockerfile, image_name, tag, CONFIG.get('build_args', {}))

def menu_push_only():
    """プッシュのみを実行"""
    print("\n=== プッシュのみを実行 ===")
    image_name = get_input("イメージ名", CONFIG['defaults']['image_name'])
    tag = get_input("タグ", CONFIG['defaults']['tag'])
    username = get_input("Docker Hubユーザー名 (省略可)", CONFIG['docker_hub']['username'])
    
    if confirm(f"{image_name}:{tag} をプッシュしますか？"):
        push_image(image_name, tag, username or None)

def menu_build_and_push():
    """ビルド + プッシュを実行"""
    print("\n=== ビルド + プッシュを実行 ===")
    dockerfile = get_input("Dockerfileのパス", CONFIG['defaults']['dockerfile'])
    image_name = get_input("イメージ名", CONFIG['defaults']['image_name'])
    tag = get_input("タグ", CONFIG['defaults']['tag'])
    username = get_input("Docker Hubユーザー名 (省略可)", CONFIG['docker_hub']['username'])
    
    if confirm(f"{image_name}:{tag} をビルドしてプッシュしますか？"):
        build_and_push(
            dockerfile=dockerfile,
            image_name=image_name,
            tag=tag,
            username=username or None,
            build_args=CONFIG.get('build_args', {})
        )

def menu_full_workflow():
    """完全なワークフローを実行（ビルド + タグ付け + プッシュ）"""
    print("\n=== 完全なワークフローを実行 ===")
    
    # ビルド
    dockerfile = get_input("Dockerfileのパス", CONFIG['defaults']['dockerfile'])
    image_name = get_input("ローカルイメージ名", CONFIG['defaults']['image_name'])
    tag = get_input("タグ", CONFIG['defaults']['tag'])
    
    if not confirm(f"{image_name}:{tag} をビルドしますか？"):
        return
    
    if not build_image(dockerfile, image_name, tag, CONFIG.get('build_args', {})):
        return
    
    # リモートリポジトリ設定
    username = get_input("Docker Hubユーザー名", CONFIG['docker_hub']['username'])
    remote_image = get_input("リモートイメージ名", image_name)
    
    # タグ付け
    if not tag_image(image_name, f"{username}/{remote_image}", tag, tag):
        return
    
    # プッシュ
    if confirm(f"{username}/{remote_image}:{tag} をプッシュしますか？"):
        push_image(remote_image, tag, username)

def interactive_main():
    """対話モードのメイン関数"""
    if not check_docker_installed() or not check_docker_login():
        return
    
    while True:
        print("\n" + "=" * 60)
        print("🐳 Docker ツール")
        print("=" * 60)
        print("1. 🔨 ビルドのみ")
        print("2. 📤 プッシュのみ")
        print("3. 🔨📤 ビルド + プッシュ")
        print("4. 🚀 完全なワークフロー (ビルド + タグ付け + プッシュ)")
        print("5. ⚙️ 現在の設定を表示")
        print("6. ❌ 終了")
        print("=" * 60)
        
        try:
            choice = input("\n選択してください (1-6): ").strip()
            
            if choice == "1":
                menu_build_only()
            elif choice == "2":
                menu_push_only()
            elif choice == "3":
                menu_build_and_push()
            elif choice == "4":
                menu_full_workflow()
            elif choice == "5":
                show_settings()
            elif choice == "6":
                print("\n終了します。")
                break
            else:
                print("\n無効な選択です。1-6の数字を入力してください。")
        except KeyboardInterrupt:
            print("\n\n操作がキャンセルされました。")
            break
        except Exception as e:
            logger.error(f"エラーが発生しました: {e}")
            if confirm("続行しますか？"):
                continue
            break

def main():
    """コマンドラインインターフェース"""
    parser = argparse.ArgumentParser(description='Docker ビルド・プッシュツール')
    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')
    
    # ビルドコマンド
    build_parser = subparsers.add_parser('build', help='Dockerイメージをビルド')
    build_parser.add_argument('-f', '--dockerfile', default=CONFIG['defaults']['dockerfile'],
                            help=f'Dockerfileのパス (デフォルト: {CONFIG["defaults"]["dockerfile"]})')
    build_parser.add_argument('-i', '--image', default=CONFIG['defaults']['image_name'],
                            help=f'イメージ名 (デフォルト: {CONFIG["defaults"]["image_name"]})')
    build_parser.add_argument('-t', '--tag', default=CONFIG['defaults']['tag'],
                            help=f'タグ (デフォルト: {CONFIG["defaults"]["tag"]})')
    
    # プッシュコマンド
    push_parser = subparsers.add_parser('push', help='Dockerイメージをプッシュ')
    push_parser.add_argument('-i', '--image', default=CONFIG['defaults']['image_name'],
                           help=f'イメージ名 (デフォルト: {CONFIG["defaults"]["image_name"]})')
    push_parser.add_argument('-t', '--tag', default=CONFIG['defaults']['tag'],
                           help=f'タグ (デフォルト: {CONFIG["defaults"]["tag"]})')
    push_parser.add_argument('-u', '--username', default=CONFIG['docker_hub']['username'],
                           help=f'Docker Hubユーザー名 (デフォルト: {CONFIG["docker_hub"]["username"]})')
    
    # ビルド＆プッシュコマンド
    build_push_parser = subparsers.add_parser('build-push', help='ビルドしてプッシュ')
    build_push_parser.add_argument('-f', '--dockerfile', default=CONFIG['defaults']['dockerfile'],
                                 help=f'Dockerfileのパス (デフォルト: {CONFIG["defaults"]["dockerfile"]})')
    build_push_parser.add_argument('-i', '--image', default=CONFIG['defaults']['image_name'],
                                 help=f'イメージ名 (デフォルト: {CONFIG["defaults"]["image_name"]})')
    build_push_parser.add_argument('-t', '--tag', default=CONFIG['defaults']['tag'],
                                 help=f'タグ (デフォルト: {CONFIG["defaults"]["tag"]})')
    build_push_parser.add_argument('-u', '--username', default=CONFIG['docker_hub']['username'],
                                 help=f'Docker Hubユーザー名 (デフォルト: {CONFIG["docker_hub"]["username"]})')
    
    # インタラクティブモード
    subparsers.add_parser('interactive', help='対話モードで起動')
    
    # 設定表示
    subparsers.add_parser('config', help='現在の設定を表示')
    
    args = parser.parse_args()
    
    if not args.command:
        interactive_main()
        return
    
    try:
        if args.command == 'build':
            build_image(args.dockerfile, args.image, args.tag, CONFIG.get('build_args', {}))
        elif args.command == 'push':
            push_image(args.image, args.tag, args.username)
        elif args.command == 'build-push':
            build_and_push(
                dockerfile=args.dockerfile,
                image_name=args.image,
                tag=args.tag,
                username=args.username,
                build_args=CONFIG.get('build_args', {})
            )
        elif args.command == 'interactive':
            interactive_main()
        elif args.command == 'config':
            show_settings()
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
