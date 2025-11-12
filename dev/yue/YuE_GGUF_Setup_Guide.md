# YuE GGUF Model Installation Guide

This guide will help you install and set up the YuE GGUF model on your Windows PC.

## Prerequisites

- Windows 10/11
- At least 8GB RAM (16GB+ recommended)
- Sufficient disk space (model files are typically 4-8GB depending on quantization)

## Step 1: Download GGUF Loader

GGUF Loader is a user-friendly Windows application that allows you to run GGUF models locally without Python or command-line interfaces.

1. Visit: https://ggufloader.github.io/
2. Download the Windows standalone executable
3. Run the installer and follow the on-screen instructions

## Step 2: Download the YuE GGUF Model

The YuE model is available on Hugging Face with different quantization levels:

### Model Repository
- **Hugging Face URL**: https://huggingface.co/Aryanne/YuE-s1-7B-anneal-en-cot-Q6_K-GGUF

### Available Quantizations
- **Q4_0**: Lower memory usage, faster inference (recommended for 8GB RAM)
- **Q6_K**: Balanced performance and quality (recommended for 16GB+ RAM)
- **Q8_0**: Higher precision, slower inference (requires more RAM)

### Download Options

**Option A: Manual Download**
1. Visit the Hugging Face repository link above
2. Click on "Files and versions" tab
3. Download the desired `.gguf` file (e.g., `yue-s1-7b-anneal-en-cot-q6_k.gguf`)
4. Save it to a folder on your PC (e.g., `C:\Models\YuE\`)

**Option B: Using the Download Script**
Run the provided PowerShell script `download_yue_model.ps1` to automatically download the model.

## Step 3: Load the Model in GGUF Loader

1. Open GGUF Loader application
2. Click the "Load Model" button
3. Navigate to the folder where you saved the YuE GGUF model file
4. Select the `.gguf` file and click "Open"
5. Wait for the model to load (this may take a few minutes)

## Step 4: Start Using the Model

Once loaded, you can:
- Interact with the model through the GGUF Loader interface
- All processing happens locally on your machine
- No internet connection required after initial download
- Your data remains private and secure

## Troubleshooting

### Model Won't Load
- Ensure you have enough RAM (check Task Manager)
- Try a lower quantization (Q4_0 instead of Q6_K or Q8_0)
- Close other memory-intensive applications

### Slow Performance
- Use a lower quantization level
- Ensure you're using GPU acceleration if available
- Check system resources in Task Manager

### Download Issues
- Ensure you have a stable internet connection
- Model files are large (4-8GB), so download may take time
- Check your disk space before downloading

## Alternative: Using llama.cpp (Advanced)

If you prefer command-line tools, you can also use llama.cpp:

1. Download llama.cpp from: https://github.com/ggerganov/llama.cpp
2. Download the Windows binaries or compile from source
3. Use the command: `llama-cli.exe -m path\to\yue-model.gguf -p "Your prompt here"`

## Model Information

- **Model Name**: YuE-s1-7B
- **Size**: ~7B parameters
- **Format**: GGUF
- **Language**: English (with CoT - Chain of Thought capabilities)

## Support

For issues with:
- **GGUF Loader**: Check https://ggufloader.github.io/ for support
- **Model**: Check the Hugging Face repository for discussions
- **llama.cpp**: Visit https://github.com/ggerganov/llama.cpp

