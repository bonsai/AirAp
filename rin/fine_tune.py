# 必要なライブラリをインポート
from transformers import (
    AutoModelForCausalLM, # テキスト生成モデル（GPT-2とか）をロードするための機能
    AutoTokenizer,       # トークナイザー（文章をモデルが理解できる数字に変える機能）
    TrainingArguments,   # 特訓（トレーニング）の設定
    Trainer,             # 特訓を実行する機能
)
from datasets import load_dataset, Dataset # データセットを扱う機能

# 1. 超重要！特訓で使うモデル名とトークナイザー名
MODEL_NAME = "rinna/japanese-gpt2-medium"

# 2. 特訓のデータパス
# Dockerfileでこの場所に置いた「ラップの歌詞データ」を使うよ！
DATA_PATH = "rap_lyrics.txt"

# 3. モデルとトークナイザーをロード！
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

# GPT-2系のモデルは「文章の切れ目」を教えるためのパディングトークンがない場合があるから追加するべし！
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


# 5. 特訓の設定を決めるべし！（この設定でモデルの出来が決まる！）
training_args = TrainingArguments(
    output_dir="./rap_model_results", # 特訓後のモデルを保存する場所
    num_train_epochs=3,               # 特訓の回数（回数が多すぎると過学習になっちゃうから注意！）
    per_device_train_batch_size=4,    # 一度に学習させるデータの量（GPUのメモリに合わせて調整！）
    learning_rate=5e-5,               # 学習の速さ
    save_total_limit=2,               # モデルのチェックポイントを保存する数
    logging_dir='./logs',
    logging_steps=100,
    fp16=True,                        # GPUを使うなら、処理を速くするための設定（必須！）
    report_to="none",                 # 今回はロギング機能を使わない
)

# 6. 特訓マシーン（Trainer）をセットアップ！
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=lm_datasets["train"],
    tokenizer=tokenizer,
)

# 7. 特訓スタート！マジでアツい！
print("🔥 特訓（ファインチューニング）開始！アゲ〜！ 🔥")
trainer.train()

# 8. 完成したモデルを保存するべし！
trainer.save_model("./best_rap_model")
print("✅ 特訓完了！最強のラップモデルが './best_rap_model' に爆誕したよ！")