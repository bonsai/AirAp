"""
GGUFモデルローダー
rinnaとYuEのGGUFモデルをロードして使用
"""
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
import os

# llama-cpp-pythonのインポート
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")


class GGUFModelLoader:
    """GGUFモデルのローダーとマネージャー"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        Args:
            models_dir: モデルファイルのベースディレクトリ
        """
        if models_dir is None:
            models_dir = Path("/app")
        self.models_dir = Path(models_dir)
        self.models: Dict[str, Llama] = {}
        self.model_paths: Dict[str, Path] = {}
        
        # デフォルトのモデルパス
        self._setup_default_paths()
    
    def _setup_default_paths(self):
        """デフォルトのモデルパスを設定"""
        # YuEモデル
        yue_path = self.models_dir / "yue" / "Models" / "YuE"
        yue_files = list(yue_path.glob("*.gguf")) if yue_path.exists() else []
        if yue_files:
            self.model_paths["yue"] = yue_files[0]
            logger.info(f"Found YuE model: {self.model_paths['yue']}")
        
        # rinnaモデル（GGUF形式）
        rinna_paths = [
            self.models_dir / "rin" / "models",
            self.models_dir / "rinna" / "models",
            self.models_dir / "models" / "rinna"
        ]
        for rinna_path in rinna_paths:
            if rinna_path.exists():
                rinna_files = list(rinna_path.glob("*.gguf"))
                if rinna_files:
                    self.model_paths["rinna"] = rinna_files[0]
                    logger.info(f"Found rinna model: {self.model_paths['rinna']}")
                    break
        
        # 環境変数からモデルパスを取得
        if "YUE_MODEL_PATH" in os.environ:
            self.model_paths["yue"] = Path(os.environ["YUE_MODEL_PATH"])
        if "RINNA_MODEL_PATH" in os.environ:
            self.model_paths["rinna"] = Path(os.environ["RINNA_MODEL_PATH"])
    
    def load_model(
        self,
        model_name: str = "yue",
        n_ctx: int = 2048,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = 0,
        verbose: bool = False
    ) -> Optional[Llama]:
        """
        モデルをロード
        
        Args:
            model_name: モデル名 ("yue" または "rinna")
            n_ctx: コンテキストサイズ
            n_threads: スレッド数（Noneの場合は自動）
            n_gpu_layers: GPUレイヤー数（0の場合はCPUのみ）
            verbose: 詳細ログ出力
        
        Returns:
            Llamaインスタンス、またはNone（エラー時）
        """
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python is not available")
            return None
        
        # 既にロードされている場合はそれを返す
        if model_name in self.models:
            logger.info(f"Model {model_name} already loaded")
            return self.models[model_name]
        
        # モデルパスの確認
        if model_name not in self.model_paths:
            logger.error(f"Model path not found for {model_name}")
            logger.info(f"Available models: {list(self.model_paths.keys())}")
            return None
        
        model_path = self.model_paths[model_name]
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None
        
        try:
            logger.info(f"Loading {model_name} model from {model_path}")
            logger.info(f"Model size: {model_path.stat().st_size / (1024**3):.2f} GB")
            
            # モデルをロード
            model = Llama(
                model_path=str(model_path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=verbose
            )
            
            self.models[model_name] = model
            logger.success(f"Successfully loaded {model_name} model")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    def generate(
        self,
        prompt: str,
        model_name: str = "yue",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """
        テキスト生成
        
        Args:
            prompt: プロンプト
            model_name: 使用するモデル名
            max_tokens: 最大トークン数
            temperature: 温度パラメータ
            top_p: top-pサンプリング
            top_k: top-kサンプリング
            repeat_penalty: 繰り返しペナルティ
            stop: 停止トークン
            **kwargs: その他のパラメータ
        
        Returns:
            生成されたテキスト
        """
        model = self.load_model(model_name)
        if model is None:
            raise RuntimeError(f"Failed to load model: {model_name}")
        
        try:
            # モデルで生成
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                **kwargs
            )
            
            # レスポンスからテキストを抽出
            if isinstance(response, dict):
                text = response.get("choices", [{}])[0].get("text", "")
            elif hasattr(response, "choices"):
                text = response.choices[0].text
            else:
                text = str(response)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise
    
    def unload_model(self, model_name: str):
        """モデルをアンロード"""
        if model_name in self.models:
            del self.models[model_name]
            logger.info(f"Unloaded model: {model_name}")
    
    def unload_all(self):
        """すべてのモデルをアンロード"""
        self.models.clear()
        logger.info("All models unloaded")


# グローバルインスタンス
_loader: Optional[GGUFModelLoader] = None


def get_loader(models_dir: Optional[Path] = None) -> GGUFModelLoader:
    """グローバルローダーインスタンスを取得"""
    global _loader
    if _loader is None:
        _loader = GGUFModelLoader(models_dir)
    return _loader


def generate_with_gguf(
    prompt: str,
    model_name: str = "yue",
    **kwargs
) -> str:
    """
    GGUFモデルを使用してテキスト生成（簡易関数）
    
    Args:
        prompt: プロンプト
        model_name: モデル名 ("yue" または "rinna")
        **kwargs: 生成パラメータ
    
    Returns:
        生成されたテキスト
    """
    loader = get_loader()
    return loader.generate(prompt, model_name=model_name, **kwargs)

