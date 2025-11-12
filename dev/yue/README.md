# YuE GGUF モデル インストールガイド

このディレクトリには、YuE GGUFモデルをPCに完全にセットアップするための統合スクリプトが含まれています。

## クイックスタート

### 基本的な使用方法

PowerShellで以下のコマンドを実行してください：

```powershell
.\install_yue_gguf.ps1
```

スクリプトは以下の処理を自動的に実行します：

1. ✅ システム要件の確認（RAM、ディスク容量）
2. ✅ Pythonの確認とインストール（必要に応じて）
3. ✅ GGUF Loaderの確認とインストール（必要に応じて）
4. ✅ モデルディレクトリの作成
5. ✅ YuE GGUFモデルのダウンロード

### オプション

#### 量子化レベルを指定して実行

```powershell
.\install_yue_gguf.ps1 -Quantization Q6_K
```

利用可能な量子化レベル：
- `Q4_0` - 低メモリ、高速（8GB RAM推奨）
- `Q6_K` - バランス型（16GB+ RAM推奨）
- `Q8_0` - 高精度、低速（より多くのRAMが必要）

#### 自動インストールモード

```powershell
.\install_yue_gguf.ps1 -AutoInstall
```

ユーザー入力なしで自動的にインストールを進めます。

#### Pythonのインストールをスキップ

```powershell
.\install_yue_gguf.ps1 -SkipPython
```

## システム要件

- **OS**: Windows 10/11
- **RAM**: 最低8GB（16GB以上推奨）
- **ディスク容量**: 最低10GBの空き容量
- **Python**: 3.8以上（自動インストール可能）

## インストールされるアプリケーション

### 1. Python
- インストール方法: winget経由、または手動ダウンロード
- 用途: GGUF Loader（Pythonパッケージ版）の実行に必要

### 2. GGUF Loader
- インストール方法: 
  - Pythonパッケージ: `pip install ggufloader`
  - またはスタンドアロンアプリ: https://ggufloader.github.io/
- 用途: GGUF形式のモデルを実行するためのアプリケーション

## ダウンロードされるモデル

- **モデル名**: YuE-s1-7B
- **リポジトリ**: https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF
- **保存先**: `Models\YuE\` ディレクトリ
- **ファイルサイズ**: 約4-8GB（量子化レベルによる）

## 使用方法

### 1. スクリプトの実行

```powershell
cd "G:\My Drive\yue"
.\install_yue_gguf.ps1
```

### 2. 量子化レベルの選択

スクリプト実行時に、システムのRAMに応じて適切な量子化レベルを選択してください：

- **8GB RAM以下**: Q4_0を推奨
- **16GB RAM以上**: Q6_Kを推奨
- **32GB RAM以上**: Q8_0を推奨

### 3. モデルの使用

インストール完了後：

1. GGUF Loaderを起動
2. 「Load Model」ボタンをクリック
3. `Models\YuE\` フォルダからダウンロードした`.gguf`ファイルを選択
4. モデルの読み込み完了後、チャットを開始

## トラブルシューティング

### Pythonが見つからない

- スクリプトが自動的にインストールを試みます
- 手動インストール: https://www.python.org/downloads/
- インストール時は「Add Python to PATH」にチェックを入れてください

### GGUF Loaderが見つからない

- Pythonパッケージ版: `pip install ggufloader`
- スタンドアロン版: https://ggufloader.github.io/ からダウンロード

### モデルのダウンロードが失敗する

- インターネット接続を確認してください
- モデルファイルは大きいため、ダウンロードに時間がかかります
- 手動ダウンロード: https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF

### メモリ不足エラー

- より低い量子化レベル（Q4_0）を試してください
- 他のアプリケーションを閉じてメモリを確保してください
- システムのRAMを確認してください

## ファイル構成

```
yue/
├── install_yue_gguf.ps1    # 統合インストールスクリプト
├── README.md               # このファイル
└── Models/
    └── YuE/
        └── yue-s1-7b-anneal-en-cot-*.gguf  # ダウンロードされたモデル
```

## 参考リンク

- **GGUF Loader**: https://ggufloader.github.io/
- **YuEモデル**: https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF
- **Python**: https://www.python.org/

## サポート

問題が発生した場合：
1. スクリプトのエラーメッセージを確認
2. システム要件を満たしているか確認
3. 上記のトラブルシューティングを参照

