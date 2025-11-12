
"""
対話式のDockerイメージビルド・プッシュスクリプト
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
    )
    from .config import (
        DOCKER_HUB_USERNAME,
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


def interactive_main():
    """
    対話式のメイン関数
    """
    logger.info("🚀 Welcome to the Interactive Docker Build & Push tool!")
    
    # --- Dockerの確認 ---
    if not check_docker_installed():
        logger.error("Docker is not installed. Please install it to continue.")
        return
    
    logger.info("✅ Docker is installed.")
    
    if not check_docker_login():
        logger.warning("You are not logged into Docker Hub.")
        if confirm("Do you want to log in now? (opens a new terminal)"):
            logger.info("Please run 'docker login' in a new terminal and then continue here.")
            input("Press Enter to continue...")
    else:
        logger.info("✅ Logged into Docker Hub.")

    # --- ビルド ---
    if confirm("\nDo you want to build a Docker image?"):
        dockerfile = get_input("Dockerfile path", DEFAULT_DOCKERFILE)
        image_name = get_input("Image name", DEFAULT_IMAGE_NAME)
        tag = get_input("Image tag", DEFAULT_TAG)
        
        if build_image(dockerfile, image_name, tag):
            logger.success(f"Image '{image_name}:{tag}' built successfully.")
        else:
            logger.error("Build failed. Exiting.")
            return
    else:
        logger.info("Skipping build step.")
        image_name = get_input("Enter the existing image name to use", DEFAULT_IMAGE_NAME)
        tag = get_input("Enter the existing tag to use", DEFAULT_TAG)


    # --- プッシュ ---
    if confirm("\nDo you want to push the image to Docker Hub?"):
        username = get_input("Docker Hub username", DOCKER_HUB_USERNAME)
        
        # タグ付け
        full_image_name = f"{username}/{image_name}"
        if not tag_image(image_name, full_image_name, tag, tag):
            logger.error("Tagging failed. Aborting push.")
            return
            
        # プッシュ
        if push_image(image_name, tag, username):
            logger.success("Image pushed successfully!")
        else:
            logger.error("Push failed.")
    else:
        logger.info("Skipping push step.")

    logger.info("\n🎉 All done!")


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
