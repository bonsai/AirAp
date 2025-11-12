# Docker ツール

このリポジトリには、Dockerイメージのビルドとプッシュを効率的に行うためのツールが含まれています。

## 機能

- 対話型インターフェースによる直感的な操作
- コマンドラインからの直接実行
- YAMLベースの設定管理
- ビルド引数のサポート
- 詳細なロギング

## セットアップ

1. 必要なパッケージをインストール:
   ```bash
   pip install -r requirements.txt
   ```

2. `config.yaml` を必要に応じて編集:
   ```yaml
   docker_hub:
     username: "your_username"
     repository: "your_repository"
   
   defaults:
     dockerfile: "Dockerfile"
     image_name: "my-image"
     tag: "latest"
   ```

## 使い方

### 対話モードで実行
```bash
python docker_tools.py interactive
```

### コマンドラインから直接実行

#### ビルドのみ
```bash
python docker_tools.py build -f Dockerfile -i my-image -t v1.0
```

#### プッシュのみ
```bash
python docker_tools.py push -i my-image -t v1.0 -u username
```

#### ビルドしてプッシュ
```bash
python docker_tools.py build-push -f Dockerfile -i my-image -t v1.0 -u username
```

#### 設定を表示
```bash
python docker_tools.py config
```

## 設定オプション

`config.yaml` で以下の設定が可能です:

- `docker_hub`: Docker Hubの設定
  - `username`: Docker Hubのユーザー名
  - `repository`: リポジトリ名
  - `full_name`: 自動設定 (username/repository)
  - `url`: Docker HubのURL

- `defaults`: デフォルト値
  - `dockerfile`: デフォルトのDockerfileパス
  - `image_name`: デフォルトのイメージ名
  - `tag`: デフォルトのタグ

- `build_args`: ビルド引数
  ```yaml
  build_args:
    ARG1: value1
    ARG2: value2
  ```

- `logging`: ログ設定
  - `level`: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `file`: ログファイルのパス
  - `rotation`: ログローテーション設定

## ライセンス

MIT
