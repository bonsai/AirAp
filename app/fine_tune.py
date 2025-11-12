"""
歌詞生成モデルのファインチューニング
ML機能統合版: データ前処理、品質評価、改善提案を含む
"""
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
)
from datasets import load_dataset, Dataset
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger
import json

# ML分析機能をインポート
try:
    from .lyrics_ml import get_analyzer, analyze_lyrics
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML analysis features not available")

# ============================================================
# 設定
# ============================================================

# 1. モデル名
MODEL_NAME = "rinna/japanese-gpt2-medium"

# 2. データパス
DATA_PATH = "rap_lyrics.txt"
OUTPUT_DIR = "./rap_model_results"
BEST_MODEL_DIR = "./best_rap_model"

# 3. トレーニング設定
NUM_EPOCHS = 3
BATCH_SIZE = 4
LEARNING_RATE = 5e-5
MAX_LENGTH = 128

# ============================================================
# データ前処理と品質評価
# ============================================================

def preprocess_and_filter_data(data_path: str, min_quality: float = 0.5) -> List[str]:
    """
    データを前処理し、品質の低い歌詞をフィルタリング
    
    Args:
        data_path: データファイルのパス
        min_quality: 最小品質スコア
    
    Returns:
        フィルタリングされた歌詞のリスト
    """
    logger.info(f"Loading and preprocessing data from {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        raw_lyrics = f.read().strip().split('\n\n')  # 空行で区切られた歌詞
    
    if not ML_AVAILABLE:
        logger.warning("ML analysis not available, skipping quality filtering")
        return raw_lyrics
    
    analyzer = get_analyzer()
    filtered_lyrics = []
    
    for i, lyrics in enumerate(raw_lyrics):
        if not lyrics.strip():
            continue
        
        try:
            analysis = analyzer.analyze_lyrics(lyrics)
            
            if analysis.quality.overall_score >= min_quality:
                filtered_lyrics.append(lyrics)
            else:
                logger.debug(f"Filtered out lyrics {i+1}: quality={analysis.quality.overall_score:.2f}")
        except Exception as e:
            logger.warning(f"Error analyzing lyrics {i+1}: {e}")
            # エラー時は含める
            filtered_lyrics.append(lyrics)
    
    logger.info(f"Filtered {len(raw_lyrics)} -> {len(filtered_lyrics)} lyrics")
    return filtered_lyrics


def save_quality_report(lyrics_list: List[str], output_path: str):
    """品質レポートを保存"""
    if not ML_AVAILABLE:
        return
    
    analyzer = get_analyzer()
    report = {
        "total_lyrics": len(lyrics_list),
        "analyses": []
    }
    
    for lyrics in lyrics_list[:100]:  # 最初の100件のみ
        try:
            analysis = analyzer.analyze_lyrics(lyrics)
            report["analyses"].append({
                "quality_score": analysis.quality.overall_score,
                "rhyme_score": analysis.quality.rhyme_score,
                "rhythm_score": analysis.quality.rhythm_score,
                "sentiment": analysis.sentiment.dominant_emotion,
                "theme": analysis.theme,
                "word_count": analysis.word_count
            })
        except Exception:
            pass
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Quality report saved to {output_path}")


# ============================================================
# モデルとトークナイザーのロード
# ============================================================

logger.info(f"Loading model: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# パディングトークンの追加
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    model.resize_token_embeddings(len(tokenizer))


# 4. ラップの歌詞データセットを用意するべし！
# load_datasetでテキストファイルを読み込んで、データセット形式にする
raw_datasets = load_dataset('text', data_files={'train': DATA_PATH})

# 歌詞をトークナイズ（モデルが理解できる形式に変換）する関数
def tokenize_function(examples):
    # max_lengthはラップの1行やブロックの長さに合わせて調整するといいよ！
    return tokenizer(examples["text"], truncation=True, max_length=128)

tokenized_datasets = raw_datasets.map(
    tokenize_function,
    batched=True,
    num_proc=4, # PCのコア数に合わせて並列処理すると爆速！
    remove_columns=["text"],
)

# モデルの特訓に必要な形にデータを最終加工！
lm_datasets = tokenized_datasets.map(
    lambda x: {"labels": x["input_ids"].copy()}, # 入力をそのまま答え（ラベル）にする
    batched=True,
)


# ============================================================
# トレーニング設定
# ============================================================

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    save_total_limit=2,
    logging_dir='./logs',
    logging_steps=100,
    fp16=True,  # GPU使用時
    report_to="none",
    save_strategy="epoch",
    evaluation_strategy="no",  # 評価データがない場合は"no"
)

# ============================================================
# トレーナーのセットアップ
# ============================================================

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=lm_datasets["train"],
    tokenizer=tokenizer,
)

# ============================================================
# トレーニング実行
# ============================================================

if __name__ == "__main__":
    logger.info("🔥 ファインチューニング開始！ 🔥")
    
    # トレーニング実行
    train_result = trainer.train()
    
    # モデルの保存
    logger.info(f"Saving model to {BEST_MODEL_DIR}")
    trainer.save_model(BEST_MODEL_DIR)
    tokenizer.save_pretrained(BEST_MODEL_DIR)
    
    # トレーニング結果の保存
    metrics = {
        "train_loss": train_result.training_loss,
        "epochs": NUM_EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE
    }
    
    with open(f"{OUTPUT_DIR}/training_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.success(f"✅ トレーニング完了！モデルは '{BEST_MODEL_DIR}' に保存されました")
    logger.info(f"最終トレーニング損失: {train_result.training_loss:.4f}")