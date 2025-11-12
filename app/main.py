"""
AI Rapper メインエントリーポイント
FastAPIサーバーを起動
"""
import uvicorn
from loguru import logger

if __name__ == "__main__":
    logger.info("Starting AI Rapper API server...")
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
