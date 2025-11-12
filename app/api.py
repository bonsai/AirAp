"""
FastAPI API for AI Rapper
歌詞プロンプト受信 → 作曲 → MP3出力
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os
from loguru import logger

from .generator import generate_song_lyrics
from .music_composer import compose_music_from_lyrics, save_as_mp3
from .gguf_loader import get_loader

app = FastAPI(title="AI Rapper API", version="1.0.0")

# 出力ディレクトリ
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(exist_ok=True)

# 静的ファイルのマウント（UI用）
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    # ルートパスでUIを表示
    @app.get("/ui")
    async def serve_ui():
        from fastapi.responses import FileResponse
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "UI files not found"}


class LyricPrompt(BaseModel):
    """歌詞生成用のプロンプト"""
    theme: str = "love"
    style: str = "rap"
    custom_prompt: Optional[str] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    model: str = "yue"  # "yue" or "rinna"
    use_ai: bool = True  # AIモデルを使用するか


class ComposeRequest(BaseModel):
    """作曲リクエスト"""
    lyrics: Optional[str] = None
    prompt: Optional[LyricPrompt] = None
    output_filename: Optional[str] = None


@app.get("/")
async def root():
    """ヘルスチェック"""
    # 利用可能なモデルを確認
    loader = get_loader()
    available_models = list(loader.model_paths.keys())
    
    return {
        "status": "ok",
        "message": "AI Rapper API is running",
        "available_models": available_models,
        "endpoints": {
            "generate": "/generate",
            "compose": "/compose",
            "download": "/download/{filename}",
            "list": "/list"
        }
    }


@app.post("/generate")
async def generate_lyrics(prompt: LyricPrompt):
    """
    歌詞を生成するエンドポイント
    """
    try:
        logger.info(f"Generating lyrics with theme: {prompt.theme}, style: {prompt.style}")
        
        # 歌詞生成
        song = generate_song_lyrics(
            theme=prompt.theme,
            style=prompt.style,
            model=prompt.model,
            use_ai=prompt.use_ai
        )
        
        # カスタムプロンプトがある場合は上書き
        if prompt.custom_prompt:
            song.title = prompt.custom_prompt
        
        # BPMとキーを設定
        if prompt.bpm:
            song.bpm = prompt.bpm
        if prompt.key:
            song.key = prompt.key
        
        return {
            "status": "success",
            "song": {
                "title": song.title,
                "lyrics": song.lyrics,
                "bpm": song.bpm,
                "key": song.key
            }
        }
    except Exception as e:
        logger.error(f"Error generating lyrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compose")
async def compose_song(request: ComposeRequest):
    """
    歌詞から作曲してMP3を生成するエンドポイント
    プロンプトから歌詞生成 → 作曲 → MP3出力
    """
    try:
        lyrics_text = None
        song_metadata = None
        
        # 歌詞の取得
        if request.lyrics:
            # 直接歌詞が提供された場合
            lyrics_text = request.lyrics
            logger.info("Using provided lyrics")
        elif request.prompt:
            # プロンプトから歌詞生成
            logger.info(f"Generating lyrics from prompt: {request.prompt.theme}")
            song = generate_song_lyrics(
                theme=request.prompt.theme,
                style=request.prompt.style,
                model=request.prompt.model,
                use_ai=request.prompt.use_ai
            )
            lyrics_text = "\n".join(song.lyrics)
            song_metadata = {
                "title": song.title,
                "bpm": request.prompt.bpm or song.bpm,
                "key": request.prompt.key or song.key
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'lyrics' or 'prompt' must be provided"
            )
        
        # ファイル名の決定
        if request.output_filename:
            output_filename = request.output_filename
            if not output_filename.endswith('.mp3'):
                output_filename += '.mp3'
        else:
            import uuid
            output_filename = f"song_{uuid.uuid4().hex[:8]}.mp3"
        
        output_path = OUTPUT_DIR / output_filename
        
        # 作曲とMP3生成
        logger.info(f"Composing music for lyrics...")
        compose_music_from_lyrics(
            lyrics=lyrics_text,
            output_path=output_path,
            bpm=song_metadata["bpm"] if song_metadata else 120,
            key=song_metadata["key"] if song_metadata else "C"
        )
        
        # MP3ファイルの存在確認
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate MP3 file"
            )
        
        logger.success(f"Successfully generated MP3: {output_filename}")
        
        return {
            "status": "success",
            "filename": output_filename,
            "download_url": f"/download/{output_filename}",
            "metadata": song_metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error composing song: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_mp3(filename: str):
    """
    MP3ファイルをダウンロードするエンドポイント
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not filename.endswith('.mp3'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@app.get("/list")
async def list_songs():
    """
    生成されたMP3ファイルのリストを取得
    """
    try:
        files = []
        for file_path in OUTPUT_DIR.glob("*.mp3"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "download_url": f"/download/{file_path.name}"
            })
        
        return {
            "status": "success",
            "count": len(files),
            "files": sorted(files, key=lambda x: x["created"], reverse=True)
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

