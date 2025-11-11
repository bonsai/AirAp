# STEP 1: 土台となるOSを決めるべし！
# Pythonと機械学習のライブラリが使える「NVIDIA CUDA」のベースイメージを選ぶと最強！
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# STEP 2: 特訓に必要なソフトを入れるべし！
# Pythonとかpipとか、マジで使うやつ！
RUN apt-get update && \
    apt-get install -y python3 python3-pip

# STEP 3: ライブラリを一気に入れるべし！
# Hugging Faceの「transformers」と「datasets」と、計算用の「PyTorch」はマスト！
# （実際はrequirements.txtに書いてまとめて入れるのがプロのやり方だけど、今回はわかりやすく！）
RUN pip install torch transformers datasets accelerate

# STEP 4: 特訓用のコードをPCから部屋に持ってくるべし！
# 「fine_tune.py」がラップ特訓コードだよ。
# リリックデータは「rap_lyrics.txt」としてまとめてあるとするよ。
COPY fine_tune.py /app/
COPY rap_lyrics.txt /app/

# STEP 5: 部屋の作業場所を「/app」に決めるべし！
WORKDIR /app

# STEP 6: 特訓の準備完了！この設計図から作ったコンテナを動かす時の、
# デフォルトのコマンドを決めるべし！
# 特訓（ファインチューニング）用のPythonコードを実行！
CMD ["python3", "fine_tune.py"]