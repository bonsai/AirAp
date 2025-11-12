# AI Rapper - 歌詞生成・作曲・MP3出力統合システム

歌詞プロンプト受信 → AI歌詞生成（rinna/YuE GGUF） → 作曲 → MP3出力の統合システム

## 📋 目次

- [概要](#概要)
- [機能](#機能)
- [クイックスタート](#クイックスタート)
- [GGUFモデルのセットアップ](#ggufモデルのセットアップ)
- [API使用方法](#api使用方法)
- [システム要件](#システム要件)
- [トラブルシューティング](#トラブルシューティング)
- [開発ガイド](#開発ガイド)
- [参考リンク](#参考リンク)

## 概要

このシステムは、テーマとスタイルから歌詞を自動生成し、メロディーとリズムを生成してMP3ファイルとして出力するAIラッパーシステムです。Kaggle環境で動作するように最適化されており、rinna（日本語）とYuE（英語）のGGUFモデルを使用して高品質な歌詞を生成します。

## 機能

- ✅ **AI歌詞生成**: rinna/YuEのGGUFモデルを使用した高品質な歌詞生成
- ✅ **ルールベース生成**: AI不使用時のフォールバック機能
- ✅ **音楽生成**: 歌詞からメロディーとリズムを自動生成
- ✅ **MP3出力**: 完成した楽曲をMP3形式で出力
- ✅ **RESTful API**: FastAPIベースのAPIエンドポイント
- ✅ **モデル選択**: 日本語（rinna）と英語（YuE）のモデルを選択可能

## クイックスタート

### 1. Dockerイメージのビルド

```bash
cd ai_rapper
docker build -f Dockerfile.kaggle -t ai-rapper-kaggle .
```

### 2. コンテナの起動

```bash
# docker-composeを使用
docker-compose up -d

# または手動で
docker run -d -p 8000:8000 -v $(pwd)/output:/app/output ai-rapper-kaggle
```

### 3. APIの確認

ブラウザで以下にアクセス:
- **Web UI**: http://localhost:8000/ui
- **APIドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/

### 4. 最初の楽曲を生成

```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "theme": "love",
      "style": "rap",
      "model": "yue",
      "use_ai": true,
      "bpm": 120,
      "key": "C"
    }
  }'
```

レスポンスから `download_url` を取得して、MP3をダウンロード:

```bash
curl -O "http://localhost:8000/download/song_xxxxx.mp3"
```

### 5. Pythonから直接使用

```python
import requests

# 楽曲生成
response = requests.post(
    "http://localhost:8000/compose",
    json={
        "prompt": {
            "theme": "party",
            "style": "rap",
            "model": "yue",
            "use_ai": true,
            "bpm": 140
        }
    }
)

result = response.json()
print(f"Generated: {result['filename']}")

# MP3ダウンロード
mp3 = requests.get(f"http://localhost:8000{result['download_url']}")
with open(result['filename'], 'wb') as f:
    f.write(mp3.content)
```

## GGUFモデルのセットアップ

### 対応モデル

#### YuE (英語モデル)
- **モデル名**: YuE-s1-7B
- **形式**: GGUF
- **デフォルトパス**: `/app/yue/Models/YuE/*.gguf`
- **環境変数**: `YUE_MODEL_PATH`
- **推奨量子化**: Q6_K
- **メモリ**: 約6-8GB
- **用途**: 英語の歌詞生成

#### rinna (日本語モデル)
- **モデル名**: rinna/japanese-gpt2-medium (GGUF形式)
- **形式**: GGUF
- **デフォルトパス**: `/app/rin/models/*.gguf` または `/app/rinna/models/*.gguf`
- **環境変数**: `RINNA_MODEL_PATH`
- **推奨量子化**: Q4_0またはQ6_K
- **メモリ**: 約4-8GB
- **用途**: 日本語の歌詞生成

### モデルのダウンロード

#### YuEモデル

既に `yue/Models/YuE/` にモデルファイルがある場合は、そのまま使用できます。

新しいモデルをダウンロードする場合:

```bash
# Hugging Faceからダウンロード
# https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF
```

#### rinnaモデル

rinnaモデルのGGUF形式をダウンロード:

```bash
# 例: mmnga/rinna-youri-7b-gguf
# https://huggingface.co/mmnga/rinna-youri-7b-gguf
```

ダウンロードしたファイルを `/app/rin/models/` または `/app/rinna/models/` に配置してください。

### 環境変数でパスを指定

Docker環境でモデルパスを指定:

```bash
docker run -d -p 8000:8000 \
  -e YUE_MODEL_PATH=/path/to/yue.gguf \
  -e RINNA_MODEL_PATH=/path/to/rinna.gguf \
  -v $(pwd)/output:/app/output \
  ai-rapper-kaggle
```

### モデルの確認

```python
from app.gguf_loader import get_loader

loader = get_loader()
print(loader.model_paths)  # 利用可能なモデルを表示
```

## API使用方法

### APIエンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/` | ヘルスチェック・利用可能モデル表示 |
| POST | `/generate` | 歌詞を生成 |
| POST | `/compose` | 歌詞生成→作曲→MP3出力 |
| GET | `/download/{filename}` | MP3ファイルをダウンロード |
| GET | `/list` | 生成されたMP3ファイルのリスト |

### 1. 歌詞生成のみ

#### YuEモデルを使用（英語）

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "love",
    "style": "rap",
    "model": "yue",
    "use_ai": true,
    "bpm": 120,
    "key": "C"
  }'
```

#### rinnaモデルを使用（日本語）

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "愛",
    "style": "rap",
    "model": "rinna",
    "use_ai": true,
    "bpm": 120,
    "key": "C"
  }'
```

#### ルールベース生成（AI不使用）

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "love",
    "style": "rap",
    "use_ai": false
  }'
```

### 2. 歌詞生成 + 作曲 + MP3出力

```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "theme": "party",
      "style": "rap",
      "model": "yue",
      "use_ai": true,
      "bpm": 140,
      "key": "Am"
    }
  }'
```

レスポンス例:
```json
{
  "status": "success",
  "filename": "song_abc12345.mp3",
  "download_url": "/download/song_abc12345.mp3",
  "metadata": {
    "title": "Party Song",
    "bpm": 140,
    "key": "Am"
  }
}
```

### 3. 既存の歌詞から作曲

```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "Yo, this is my rap\nListen up, don'\''t look back\n",
    "output_filename": "my_song.mp3"
  }'
```

### 4. MP3ファイルのダウンロード

```bash
curl -O "http://localhost:8000/download/song_abc12345.mp3"
```

### リクエストパラメータ

#### LyricPrompt

```json
{
  "theme": "love",           // テーマ: love, party, sad など
  "style": "rap",            // スタイル: rap, pop など
  "model": "yue",            // モデル: "yue" または "rinna"
  "use_ai": true,            // AIモデルを使用するか（true/false）
  "custom_prompt": "string",  // カスタムプロンプト（オプション）
  "bpm": 120,                // テンポ（オプション）
  "key": "C"                 // キー: C, D, Am など（オプション）
}
```

#### ComposeRequest

```json
{
  "lyrics": "string",        // 直接歌詞を指定（promptと排他的）
  "prompt": { ... },         // 歌詞生成用プロンプト（lyricsと排他的）
  "output_filename": "string" // 出力ファイル名（オプション）
}
```

### Kaggle環境での使用

```python
import requests

# APIエンドポイント（Kaggle環境内のコンテナ）
API_URL = "http://localhost:8000"

# 歌詞生成と作曲
response = requests.post(
    f"{API_URL}/compose",
    json={
        "prompt": {
            "theme": "love",
            "style": "rap",
            "model": "yue",
            "use_ai": true,
            "bpm": 120,
            "key": "C"
        }
    }
)

result = response.json()
print(f"Generated: {result['filename']}")

# MP3ファイルをダウンロード
mp3_response = requests.get(f"{API_URL}{result['download_url']}")
with open(result['filename'], 'wb') as f:
    f.write(mp3_response.content)
```

## システム要件

- **OS**: Linux (Kaggle環境対応)
- **Python**: 3.11+
- **RAM**: 最低4GB（推奨8GB以上、GGUFモデル使用時は16GB以上推奨）
- **ディスク**: 最低5GBの空き容量（モデルファイル含む場合は10GB以上）

## 依存関係

### システムパッケージ
- ffmpeg (音声変換)
- fluidsynth (MIDI→WAV変換)
- timidity (MIDI再生)
- fluid-soundfont-gm (サウンドフォント)

### Pythonパッケージ
- FastAPI (Webフレームワーク)
- llama-cpp-python (GGUFモデル実行)
- music21 (MIDI処理)
- librosa (音声処理)
- pydub (音声変換)
- transformers, torch (フォールバック用)

詳細は `requirements.txt` を参照してください。

## トラブルシューティング

### モデルが見つからない

1. モデルファイルのパスを確認:
   ```python
   from app.gguf_loader import get_loader
   loader = get_loader()
   print(loader.model_paths)
   ```

2. 環境変数でパスを指定:
   ```bash
   export YUE_MODEL_PATH=/path/to/model.gguf
   export RINNA_MODEL_PATH=/path/to/rinna.gguf
   ```

### llama-cpp-pythonのインストールエラー

Kaggle環境では、事前にビルドされたwheelを使用:

```bash
# CPU版
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# GPU版（CUDA 12.1）
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### メモリ不足

- より低い量子化レベル（Q4_0）のモデルを使用
- `n_ctx`パラメータを減らす（デフォルト: 2048）
- `n_gpu_layers=0`でCPUのみ使用
- より小さなモデルを使用

### 生成速度が遅い

- GPUを使用: `n_gpu_layers`を設定
- 量子化レベルを下げる（Q4_0など）
- `n_threads`を調整

### MIDI→MP3変換が失敗する

1. fluidsynthが正しくインストールされているか確認:
   ```bash
   which fluidsynth
   ```

2. サウンドフォントが存在するか確認:
   ```bash
   ls /usr/share/sounds/sf2/
   ```

3. フォールバックとしてtimidityを使用:
   - Dockerfileでtimidityもインストール済み

### APIが応答しない

1. コンテナが起動しているか確認:
   ```bash
   docker ps
   ```

2. ログを確認:
   ```bash
   docker logs <container_id>
   # または
   docker-compose logs
   ```

### ポートが既に使用されている

```bash
# 別のポートを使用
docker run -d -p 8001:8000 ai-rapper-kaggle
```

## Web UI

### アクセス方法

サーバー起動後、ブラウザで以下にアクセス:
- **Web UI**: http://localhost:8000/ui
- **APIドキュメント**: http://localhost:8000/docs

### UI機能

#### 1. プロンプト設定
- **テーマ**: 歌詞のテーマを選択（Love, Party, Sad, Motivational, Life）
- **スタイル**: スタイルを選択（Rap, Pop）
- **AIモデル**: 使用するモデルを選択（YuE: 英語, rinna: 日本語）
- **AI使用**: AIモデルを使用するか、ルールベース生成かを選択
- **BPM**: テンポを設定（60-200）
- **キー**: 音楽のキーを選択
- **カスタムプロンプト**: 追加の指示やタイトルを入力

#### 2. 歌詞生成
「歌詞を生成」ボタンをクリックすると、設定したプロンプトに基づいて歌詞が生成されます。

#### 3. 作曲 + MP3出力
「歌詞生成 + 作曲 + MP3出力」ボタンをクリックすると：
1. 歌詞が生成される
2. メロディーとリズムが作成される
3. MP3ファイルが生成される
4. ブラウザで再生・ダウンロード可能

#### 4. 直接歌詞入力
テキストエリアに直接歌詞を入力して、「この歌詞から作曲」ボタンで作曲できます。

#### 5. 生成履歴
「生成済み楽曲一覧」ボタンで、これまでに生成した楽曲の一覧を表示し、ダウンロードや再生ができます。

### UI使用例

#### 例1: 英語のラップを生成
1. テーマ: "love"
2. スタイル: "rap"
3. AIモデル: "yue"
4. AI使用: "有効"
5. BPM: 120
6. 「歌詞生成 + 作曲 + MP3出力」をクリック

#### 例2: 日本語のラップを生成
1. テーマ: "愛"（カスタムプロンプトに記入）
2. スタイル: "rap"
3. AIモデル: "rinna"
4. AI使用: "有効"
5. 「歌詞生成 + 作曲 + MP3出力」をクリック

#### 例3: 既存の歌詞から作曲
1. 「直接歌詞を入力」セクションのテキストエリアに歌詞を入力
2. 「この歌詞から作曲」をクリック

## 開発ガイド

### ローカル開発環境

```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# サーバーを起動
python app/main.py
```

### テスト

```bash
# APIテスト
curl http://localhost:8000/

# 歌詞生成テスト
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"theme": "love", "style": "rap", "model": "yue", "use_ai": true}'

# テストスクリプトの実行
python -m pytest tests/
# または
python tests/test_api.py
```

### コード例: GGUFモデルの直接使用

```python
from app.gguf_loader import generate_with_gguf, get_loader

# 簡易関数を使用
lyrics = generate_with_gguf(
    prompt="Generate rap lyrics about love",
    model_name="yue",
    max_tokens=512,
    temperature=0.8
)

# ローダーを直接使用
loader = get_loader()
model = loader.load_model("yue", n_ctx=2048, n_gpu_layers=0)
text = loader.generate(
    "Generate lyrics",
    model_name="yue",
    max_tokens=256
)
```

### コンテナの停止

```bash
docker-compose down
# または
docker stop ai-rapper-kaggle
```

### テスト

テストは `tests/` ディレクトリにあります:

```bash
# すべてのテストを実行
python -m pytest tests/

# 個別のテストを実行
python tests/test_api.py
python tests/test_generator.py
python tests/test_ml_analysis.py
```

### ビルドとデプロイ

DockerイメージのビルドとDocker Hubへのアップロード:

```bash
# scriptsディレクトリのスクリプトを使用
python scripts/build_and_push.py --username YOUR_USERNAME

# 詳細は scripts/README_BUILD.md を参照
```

## 参考リンク

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [music21 Documentation](http://web.mit.edu/music21/)
- [Kaggle Docker Images](https://github.com/Kaggle/docker-python)
- [YuE Model](https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF)
- [rinna Models](https://huggingface.co/rinna)

---

## ライセンス

このプロジェクトのライセンス情報は各コンポーネントのライセンスに従います。

