"""
DockerイメージのビルドとDocker Hubへのアップロードスクリプト
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional
import argparse
from loguru import logger

# 設定をインポート
try:
    from .config import (
        DOCKER_HUB_USERNAME,
        DOCKER_HUB_REPOSITORY,
        DOCKER_HUB_FULL_NAME,
        DOCKER_HUB_URL,
        DEFAULT_DOCKERFILE,
        DEFAULT_IMAGE_NAME,
        DEFAULT_TAG
    )
except ImportError:
    # フォールバック（config.pyがない場合）
    DOCKER_HUB_USERNAME = None
    DOCKER_HUB_REPOSITORY = None
    DOCKER_HUB_FULL_NAME = None
    DOCKER_HUB_URL = None
    DEFAULT_DOCKERFILE = "Dockerfile.kaggle"
    DEFAULT_IMAGE_NAME = "ai-rapper-kaggle"
    DEFAULT_TAG = "latest"

# ログ設定
logger.add("build.log", rotation="10 MB", level="INFO")


def run_command(cmd: list, check: bool = True) -> tuple[int, str, str]:
    """
    コマンドを実行
    
    Args:
        cmd: 実行するコマンドのリスト
        check: エラー時に例外を発生させるか
    
    Returns:
        (returncode, stdout, stderr)のタプル
    """
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
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
        logger.error(f"Command failed: {e}")
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
        logger.error("Docker is not installed or not in PATH")
        return False


def check_docker_login() -> bool:
    """Docker Hubにログインしているか確認"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def build_image(
    dockerfile: Optional[str] = None,
    image_name: Optional[str] = None,
    tag: Optional[str] = None,
    build_args: Optional[dict] = None
) -> bool:
    """
    Dockerイメージをビルド
    
    Args:
        dockerfile: Dockerfileのパス
        image_name: イメージ名
        tag: タグ
        build_args: ビルド引数
    
    Returns:
        成功したかどうか
    """
    # デフォルト値の設定
    dockerfile = dockerfile or DEFAULT_DOCKERFILE
    image_name = image_name or DEFAULT_IMAGE_NAME
    tag = tag or DEFAULT_TAG
    
    if not Path(dockerfile).exists():
        logger.error(f"Dockerfile not found: {dockerfile}")
        return False
    
    logger.info(f"Building Docker image: {image_name}:{tag}")
    
    cmd = [
        "docker", "build",
        "-f", dockerfile,
        "-t", f"{image_name}:{tag}",
        "."
    ]
    
    # ビルド引数を追加
    if build_args:
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])
    
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode == 0:
        logger.success(f"✅ Image built successfully: {image_name}:{tag}")
        return True
    else:
        logger.error(f"❌ Build failed: {stderr}")
        return False


def tag_image(
    source_image: str,
    target_image: str,
    source_tag: str = "latest",
    target_tag: Optional[str] = None
) -> bool:
    """
    イメージにタグを付ける
    
    Args:
        source_image: ソースイメージ名
        target_image: ターゲットイメージ名
        source_tag: ソースタグ
        target_tag: ターゲットタグ（Noneの場合はsource_tagと同じ）
    
    Returns:
        成功したかどうか
    """
    if target_tag is None:
        target_tag = source_tag
    
    logger.info(f"Tagging {source_image}:{source_tag} as {target_image}:{target_tag}")
    
    cmd = [
        "docker", "tag",
        f"{source_image}:{source_tag}",
        f"{target_image}:{target_tag}"
    ]
    
    returncode, _, _ = run_command(cmd, check=False)
    return returncode == 0


def push_image(
    image_name: str,
    tag: str = "latest",
    username: Optional[str] = None
) -> bool:
    """
    Docker Hubにイメージをプッシュ
    
    Args:
        image_name: イメージ名
        tag: タグ
        username: Docker Hubのユーザー名（指定時は username/image_name 形式）
    
    Returns:
        成功したかどうか
    """
    if username:
        full_image_name = f"{username}/{image_name}"
    else:
        full_image_name = image_name
    
    logger.info(f"Pushing image to Docker Hub: {full_image_name}:{tag}")
    
    # ログイン確認
    if not check_docker_login():
        logger.warning("Docker login status unclear. Make sure you're logged in:")
        logger.info("Run: docker login")
    
    cmd = ["docker", "push", f"{full_image_name}:{tag}"]
    
    returncode, stdout, stderr = run_command(cmd, check=False)
    
    if returncode == 0:
        logger.success(f"✅ Image pushed successfully: {full_image_name}:{tag}")
        logger.info(f"Docker Hub URL: https://hub.docker.com/r/{full_image_name}")
        return True
    else:
        logger.error(f"❌ Push failed: {stderr}")
        return False


def build_and_push(
    dockerfile: Optional[str] = None,
    image_name: Optional[str] = None,
    tag: Optional[str] = None,
    username: Optional[str] = None,
    build_args: Optional[dict] = None,
    skip_build: bool = False,
    skip_push: bool = False
) -> bool:
    """
    ビルドとプッシュを一括実行
    
    Args:
        dockerfile: Dockerfileのパス
        image_name: イメージ名
        tag: タグ
        username: Docker Hubのユーザー名（Noneの場合はconfig.pyから取得）
        build_args: ビルド引数
        skip_build: ビルドをスキップ
        skip_push: プッシュをスキップ
    
    Returns:
        成功したかどうか
    """
    # デフォルト値の設定
    dockerfile = dockerfile or DEFAULT_DOCKERFILE
    image_name = image_name or DEFAULT_IMAGE_NAME
    tag = tag or DEFAULT_TAG
    username = username or DOCKER_HUB_USERNAME
    
    # Dockerの確認
    if not check_docker_installed():
        return False
    
    # ビルド
    if not skip_build:
        if not build_image(dockerfile, image_name, tag, build_args):
            return False
    
    # タグ付け（usernameが指定されている場合）
    if username and not skip_push:
        full_image_name = f"{username}/{image_name}"
        if not tag_image(image_name, full_image_name, tag, tag):
            logger.warning("Tagging failed, but continuing...")
        
        # Docker Hub URLを表示
        if DOCKER_HUB_URL:
            logger.info(f"Docker Hub URL: {DOCKER_HUB_URL}")
    
    # プッシュ
    if not skip_push:
        if not push_image(image_name, tag, username):
            return False
    
    logger.success("🎉 Build and push completed successfully!")
    if DOCKER_HUB_URL and username:
        logger.info(f"View on Docker Hub: {DOCKER_HUB_URL}")
    return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Build and push Docker image to Docker Hub"
    )
    
    parser.add_argument(
        "--dockerfile",
        "-f",
        default=None,
        help=f"Dockerfile path (default: {DEFAULT_DOCKERFILE})"
    )
    
    parser.add_argument(
        "--image-name",
        "-i",
        default=None,
        help=f"Image name (default: {DEFAULT_IMAGE_NAME})"
    )
    
    parser.add_argument(
        "--tag",
        "-t",
        default=None,
        help=f"Image tag (default: {DEFAULT_TAG})"
    )
    
    parser.add_argument(
        "--username",
        "-u",
        default=None,
        help=f"Docker Hub username (default: {DOCKER_HUB_USERNAME or 'required'})"
    )
    
    parser.add_argument(
        "--build-arg",
        action="append",
        help="Build arguments (format: KEY=VALUE, can be used multiple times)"
    )
    
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build step"
    )
    
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Skip push step"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    args = parser.parse_args()
    
    # ビルド引数のパース
    build_args = None
    if args.build_arg:
        build_args = {}
        for arg in args.build_arg:
            if "=" in arg:
                key, value = arg.split("=", 1)
                build_args[key] = value
            else:
                logger.warning(f"Invalid build arg format: {arg}")
    
    # プッシュする場合はusernameが必要
    final_username = args.username or DOCKER_HUB_USERNAME
    if not args.skip_push and not final_username:
        logger.error("--username is required for push")
        logger.info("Usage: python scripts/build_and_push.py --username YOUR_USERNAME")
        logger.info(f"Or set DOCKER_HUB_USERNAME in scripts/config.py")
        sys.exit(1)
    
    # 設定情報を表示
    if DOCKER_HUB_URL:
        logger.info(f"Docker Hub Repository: {DOCKER_HUB_FULL_NAME}")
        logger.info(f"Docker Hub URL: {DOCKER_HUB_URL}")
    
    # 実行
    success = build_and_push(
        dockerfile=args.dockerfile,
        image_name=args.image_name,
        tag=args.tag,
        username=args.username,
        build_args=build_args,
        skip_build=args.skip_build,
        skip_push=args.skip_push
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

