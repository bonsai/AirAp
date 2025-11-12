# Dockerイメージのビルドとアップロード

## クイックスタート

### 1. Docker Hubにログイン

```bash
docker login
```

### 2. ビルドとアップロード

```bash
# 設定ファイル（config.py）にリポジトリ情報が保存されている場合
python scripts/build_and_push.py

# または、ユーザー名を指定
python scripts/build_and_push.py --username vonsai
```

## 設定

### Docker Hubリポジトリ情報

`scripts/config.py` にリポジトリ情報が保存されています:

```python
DOCKER_HUB_USERNAME = "vonsai"
DOCKER_HUB_REPOSITORY = "ryup"
DOCKER_HUB_URL = "https://hub.docker.com/repository/docker/vonsai/ryup/general"
```

この設定により、デフォルトで `vonsai/ryup` リポジトリにアップロードされます。

## 使用方法

### 基本的な使用

```bash
# 設定ファイルのリポジトリ情報を使用
python scripts/build_and_push.py

# 特定のタグを指定
python scripts/build_and_push.py --tag v1.0.0

# カスタムイメージ名
python scripts/build_and_push.py --image-name my-rapper

# ビルドのみ（アップロードしない）
python scripts/build_and_push.py --skip-push

# アップロードのみ（ビルドをスキップ）
python scripts/build_and_push.py --skip-build
```

### オプション一覧

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|-----------|
| `--dockerfile` | `-f` | Dockerfileのパス | `Dockerfile.kaggle` |
| `--image-name` | `-i` | イメージ名 | `ai-rapper-kaggle` |
| `--tag` | `-t` | イメージタグ | `latest` |
| `--username` | `-u` | Docker Hubのユーザー名 | `vonsai` (config.pyから) |
| `--build-arg` | - | ビルド引数（KEY=VALUE形式） | - |
| `--skip-build` | - | ビルドをスキップ | False |
| `--skip-push` | - | アップロードをスキップ | False |

### ビルド引数の指定

```bash
python scripts/build_and_push.py \
  --build-arg YUE_MODEL_PATH=/app/models/yue.gguf \
  --build-arg RINNA_MODEL_PATH=/app/models/rinna.gguf
```

## 使用例

### 例1: 最新版をアップロード

```bash
python scripts/build_and_push.py --tag latest
```

アップロード先: `vonsai/ryup:latest`
URL: https://hub.docker.com/repository/docker/vonsai/ryup/general

### 例2: バージョンタグを付けてアップロード

```bash
python scripts/build_and_push.py --tag v1.0.0
```

アップロード先: `vonsai/ryup:v1.0.0`

### 例3: 複数のタグを付ける

```bash
# まずビルド
python scripts/build_and_push.py --tag v1.0.0 --skip-push

# 別のタグを追加
docker tag vonsai/ryup:v1.0.0 vonsai/ryup:latest

# アップロード
docker push vonsai/ryup:latest
docker push vonsai/ryup:v1.0.0
```

### 例4: ローカルでのみビルド

```bash
python scripts/build_and_push.py --skip-push
```

## 手動でのビルドとアップロード

スクリプトを使わずに手動で実行する場合:

```bash
# 1. ビルド
docker build -f Dockerfile.kaggle -t ai-rapper-kaggle:latest .

# 2. タグ付け
docker tag ai-rapper-kaggle:latest vonsai/ryup:latest

# 3. アップロード
docker push vonsai/ryup:latest
```

## Docker Hubリポジトリ

- **リポジトリ名**: `vonsai/ryup`
- **URL**: https://hub.docker.com/repository/docker/vonsai/ryup/general
- **プルコマンド**: `docker pull vonsai/ryup:latest`

## トラブルシューティング

### Dockerがインストールされていない

```bash
# Windows/Mac: Docker Desktopをインストール
# Linux:
sudo apt-get update
sudo apt-get install docker.io
```

### Docker Hubにログインできない

```bash
# ログイン
docker login

# ログイン状態を確認
docker info
```

### ビルドが失敗する

1. Dockerfileのパスを確認:
   ```bash
   ls -la Dockerfile.kaggle
   ```

2. ビルドログを確認:
   ```bash
   tail -f build.log
   ```

3. 手動でビルドしてエラーを確認:
   ```bash
   docker build -f Dockerfile.kaggle -t test-image .
   ```

### プッシュが失敗する

1. ログイン状態を確認:
   ```bash
   docker login
   ```

2. イメージ名とタグを確認:
   ```bash
   docker images
   ```

3. 権限を確認（Docker Hubでリポジトリが存在するか）

## ベストプラクティス

### タグの命名規則

- `latest`: 最新の安定版
- `v1.0.0`: セマンティックバージョニング
- `dev`: 開発版
- `beta`: ベータ版

### セキュリティ

- `.dockerignore`で機密情報を除外
- 環境変数やシークレットをイメージに含めない
- 定期的にイメージを更新

### パフォーマンス

- マルチステージビルドを使用
- 不要なファイルを除外
- キャッシュを活用

## CI/CDでの使用

### GitHub Actions例

```yaml
name: Build and Push

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        run: |
          python scripts/build_and_push.py \
            --username ${{ secrets.DOCKER_USERNAME }} \
            --tag ${GITHUB_REF#refs/tags/}
```

## 参考リンク

- [Docker Hub](https://hub.docker.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [リポジトリ](https://hub.docker.com/repository/docker/vonsai/ryup/general)
