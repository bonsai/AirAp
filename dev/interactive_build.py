"""
統合対話式Dockerイメージビルド・プッシュスクリプト
選択式メニューで操作を選択できます
"""
import sys
from loguru import logger

# 既存のビルドスクリプトから関数をインポート
try:
    from .build_and_push import (
        check_docker_installed,
        check_docker_login,
        build_image,
        tag_image,
        push_image,
        build_and_push,
    )
    from .config import (
        DOCKER_HUB_USERNAME,
        DOCKER_HUB_REPOSITORY,
        DOCKER_HUB_FULL_NAME,
        DOCKER_HUB_URL,
        DEFAULT_DOCKERFILE,
        DEFAULT_IMAGE_NAME,
        DEFAULT_TAG,
    )
except (ImportError, ModuleNotFoundError):
    print("=" * 50)
    print("ERROR: Make sure to run this script from the project root, e.g.:")
    print("python -m scripts.interactive_build")
    print("=" * 50)
    sys.exit(1)


def get_input(prompt: str, default: str = None) -> str:
    """
    ユーザーからの入力を取得する
    
    Args:
        prompt: プロンプトメッセージ
        default: デフォルト値
    
    Returns:
        ユーザーの入力
    """
    if default:
        return input(f"{prompt} (default: {default}): ") or default
    else:
        return input(f"{prompt}: ")


def confirm(prompt: str) -> bool:
    """
    ユーザーにYes/Noの確認を求める
    
    Args:
        prompt: 確認メッセージ
    
    Returns:
        YesならTrue, NoならFalse
    """
    while True:
        response = input(f"{prompt} [y/N]: ").lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no", ""]:
            return False
        print("Please enter 'y' or 'n'.")


def show_menu() -> int:
    """
    メインメニューを表示して選択を取得
    
    Returns:
        選択されたメニュー番号
    """
    print("\n" + "=" * 60)
    print("🐳 Docker Build & Push Tool")
    print("=" * 60)
    print("1. 🔨 Build only (ビルドのみ)")
    print("2. 📤 Push only (プッシュのみ)")
    print("3. 🔨📤 Build + Push (ビルド + プッシュ)")
    print("4. 🚀 Full workflow (完全なワークフロー: ビルド + タグ付け + プッシュ)")
    print("5. ⚙️  Show current settings (現在の設定を表示)")
    print("6. ❌ Exit (終了)")
    print("=" * 60)
    
    while True:
        try:
            choice = input("\nSelect an option (1-6): ").strip()
            if choice in ["1", "2", "3", "4", "5", "6"]:
                return int(choice)
            print("❌ Invalid choice. Please enter a number between 1 and 6.")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input. Please enter a number.")
            return 6


def show_settings():
    """現在の設定を表示"""
    logger.info("\n" + "=" * 60)
    logger.info("⚙️  CURRENT SETTINGS")
    logger.info("=" * 60)
    logger.info(f"Docker Hub Username: {DOCKER_HUB_USERNAME}")
    logger.info(f"Docker Hub Repository: {DOCKER_HUB_REPOSITORY}")
    logger.info(f"Full Repository Name: {DOCKER_HUB_FULL_NAME}")
    logger.info(f"Docker Hub URL: {DOCKER_HUB_URL}")
    logger.info(f"Default Dockerfile: {DEFAULT_DOCKERFILE}")
    logger.info(f"Default Image Name: {DEFAULT_IMAGE_NAME}")
    logger.info(f"Default Tag: {DEFAULT_TAG}")
    logger.info("=" * 60)
    input("\nPress Enter to continue...")


def menu_build_only():
    """ビルドのみを実行"""
    logger.info("\n" + "=" * 60)
    logger.info("🔨 BUILD CONFIGURATION")
    logger.info("=" * 60)
    dockerfile = get_input("Dockerfile path", DEFAULT_DOCKERFILE)
    image_name = get_input("Image name", DEFAULT_IMAGE_NAME)
    tag = get_input("Image tag", DEFAULT_TAG)
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting build process...")
    logger.info("=" * 60)
    
    if build_image(dockerfile, image_name, tag):
        logger.success(f"\n✅ Image '{image_name}:{tag}' built successfully.")
        return True
    else:
        logger.error("\n❌ Build failed.")
        return False


def menu_push_only():
    """プッシュのみを実行"""
    logger.info("\n" + "=" * 60)
    logger.info("📤 PUSH CONFIGURATION")
    logger.info("=" * 60)
    image_name = get_input("Image name", DEFAULT_IMAGE_NAME)
    tag = get_input("Image tag", DEFAULT_TAG)
    username = get_input("Docker Hub username", DOCKER_HUB_USERNAME)
    
    logger.info("\n" + "=" * 60)
    logger.info("🏷️  Tagging image...")
    logger.info("=" * 60)
    
    full_image_name = f"{username}/{image_name}"
    if not tag_image(image_name, full_image_name, tag, tag):
        logger.error("❌ Tagging failed. Aborting push.")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting push process...")
    logger.info("=" * 60)
    
    if push_image(image_name, tag, username):
        logger.success("\n✅ Image pushed successfully!")
        return True
    else:
        logger.error("\n❌ Push failed.")
        return False


def menu_build_and_push():
    """ビルド + プッシュを実行"""
    logger.info("\n" + "=" * 60)
    logger.info("🔨📤 BUILD & PUSH CONFIGURATION")
    logger.info("=" * 60)
    dockerfile = get_input("Dockerfile path", DEFAULT_DOCKERFILE)
    image_name = get_input("Image name", DEFAULT_IMAGE_NAME)
    tag = get_input("Image tag", DEFAULT_TAG)
    username = get_input("Docker Hub username", DOCKER_HUB_USERNAME)
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting build and push process...")
    logger.info("=" * 60)
    
    if build_and_push(
        dockerfile=dockerfile,
        image_name=image_name,
        tag=tag,
        username=username,
        skip_build=False,
        skip_push=False
    ):
        logger.success("\n✅ Build and push completed successfully!")
        return True
    else:
        logger.error("\n❌ Build and push failed.")
        return False


def menu_full_workflow():
    """完全なワークフローを実行（ビルド + タグ付け + プッシュ）"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 FULL WORKFLOW CONFIGURATION")
    logger.info("=" * 60)
    dockerfile = get_input("Dockerfile path", DEFAULT_DOCKERFILE)
    image_name = get_input("Image name", DEFAULT_IMAGE_NAME)
    tag = get_input("Image tag", DEFAULT_TAG)
    username = get_input("Docker Hub username", DOCKER_HUB_USERNAME)
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting full workflow...")
    logger.info("=" * 60)
    
    # STEP 1: ビルド
    logger.info("\n" + "=" * 60)
    logger.info("📦 STEP 1/3: Building Docker Image")
    logger.info("=" * 60)
    if not build_image(dockerfile, image_name, tag):
        logger.error("❌ Build failed. Aborting workflow.")
        return False
    
    # STEP 2: タグ付け
    logger.info("\n" + "=" * 60)
    logger.info("🏷️  STEP 2/3: Tagging Image")
    logger.info("=" * 60)
    full_image_name = f"{username}/{image_name}"
    if not tag_image(image_name, full_image_name, tag, tag):
        logger.error("❌ Tagging failed. Aborting workflow.")
        return False
    
    # STEP 3: プッシュ
    logger.info("\n" + "=" * 60)
    logger.info("📤 STEP 3/3: Pushing to Docker Hub")
    logger.info("=" * 60)
    if not push_image(image_name, tag, username):
        logger.error("❌ Push failed.")
        return False
    
    logger.success("\n" + "=" * 60)
    logger.success("🎉 Full workflow completed successfully!")
    logger.success("=" * 60)
    if DOCKER_HUB_URL:
        logger.info(f"🔗 View on Docker Hub: {DOCKER_HUB_URL}")
    return True


def interactive_main():
    """
    統合対話式のメイン関数（選択式メニュー）
    """
    logger.info("🚀 Welcome to the Docker Build & Push Tool!")
    
    # --- Dockerの確認 ---
    if not check_docker_installed():
        logger.error("❌ Docker is not installed. Please install it to continue.")
        return
    
    logger.info("✅ Docker is installed.")
    
    # Docker Hubログイン状態の確認（プッシュが必要な場合のみ）
    login_checked = False
    
    # メインループ
    while True:
        choice = show_menu()
        
        if choice == 1:  # Build only
            if menu_build_only():
                input("\nPress Enter to continue...")
        
        elif choice == 2:  # Push only
            if not login_checked:
                if not check_docker_login():
                    logger.warning("⚠️  You are not logged into Docker Hub.")
                    if confirm("Do you want to log in now? (opens a new terminal)"):
                        logger.info("Please run 'docker login' in a new terminal and then continue here.")
                        input("Press Enter to continue...")
                else:
                    logger.info("✅ Logged into Docker Hub.")
                login_checked = True
            
            if menu_push_only():
                input("\nPress Enter to continue...")
        
        elif choice == 3:  # Build + Push
            if not login_checked:
                if not check_docker_login():
                    logger.warning("⚠️  You are not logged into Docker Hub.")
                    if confirm("Do you want to log in now? (opens a new terminal)"):
                        logger.info("Please run 'docker login' in a new terminal and then continue here.")
                        input("Press Enter to continue...")
                else:
                    logger.info("✅ Logged into Docker Hub.")
                login_checked = True
            
            if menu_build_and_push():
                input("\nPress Enter to continue...")
        
        elif choice == 4:  # Full workflow
            if not login_checked:
                if not check_docker_login():
                    logger.warning("⚠️  You are not logged into Docker Hub.")
                    if confirm("Do you want to log in now? (opens a new terminal)"):
                        logger.info("Please run 'docker login' in a new terminal and then continue here.")
                        input("Press Enter to continue...")
                else:
                    logger.info("✅ Logged into Docker Hub.")
                login_checked = True
            
            if menu_full_workflow():
                input("\nPress Enter to continue...")
        
        elif choice == 5:  # Show settings
            show_settings()
        
        elif choice == 6:  # Exit
            logger.info("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    # スクリプトが直接実行された場合、
    # カレントディレクトリからの相対インポートが機能するようにパスを追加
    import os
    # このファイルの場所を基準にプロジェクトルートを特定
    # (scripts/interactive_build.py -> ai_rapper/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # モジュールとして実行されているかのように見せかける
    # これにより、`from . import ...` が機能する
    from scripts import interactive_build
    interactive_build.interactive_main()
