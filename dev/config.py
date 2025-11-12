"""
Docker Hub設定
"""
# Docker Hubリポジトリ情報
DOCKER_HUB_USERNAME = "vonsai"
DOCKER_HUB_REPOSITORY = "ryup"
DOCKER_HUB_FULL_NAME = f"{DOCKER_HUB_USERNAME}/{DOCKER_HUB_REPOSITORY}"

# Docker Hub URL
DOCKER_HUB_URL = f"https://hub.docker.com/repository/docker/{DOCKER_HUB_FULL_NAME}/general"

# デフォルト設定
DEFAULT_DOCKERFILE = "Dockerfile.kaggle"
DEFAULT_IMAGE_NAME = "ryup"
DEFAULT_TAG = "latest"


