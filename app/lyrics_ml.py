"""
歌詞の機械学習機能
品質評価、感情分析、リズム分析、テーマ分類など
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import numpy as np
from loguru import logger
from pathlib import Path

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, some ML features will be disabled")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize, sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, sentiment analysis will be limited")


@dataclass
class LyricQuality:
    """歌詞の品質評価結果"""
    overall_score: float  # 0-1のスコア
    rhyme_score: float  # 韻のスコア
    rhythm_score: float  # リズムのスコア
    coherence_score: float  # 一貫性スコア
    creativity_score: float  # 創造性スコア
    length_score: float  # 長さの適切性
    details: Dict[str, any]


@dataclass
class LyricSentiment:
    """歌詞の感情分析結果"""
    positive: float
    negative: float
    neutral: float
    compound: float
    dominant_emotion: str


@dataclass
class LyricAnalysis:
    """歌詞の包括的分析結果"""
    quality: LyricQuality
    sentiment: LyricSentiment
    theme: str
    style: str
    rhythm_pattern: Dict[str, any]
    word_count: int
    line_count: int
    avg_line_length: float
    unique_words: int
    vocabulary_richness: float


class LyricsMLAnalyzer:
    """歌詞の機械学習分析クラス"""
    
    def __init__(self):
        self.vectorizer = None
        self.theme_classifier = None
        self.style_classifier = None
        self.sentiment_analyzer = None
        
        if NLTK_AVAILABLE:
            try:
                self.sentiment_analyzer = SentimentIntensityAnalyzer()
            except LookupError:
                logger.warning("NLTK sentiment data not found, downloading...")
                try:
                    nltk.download('vader_lexicon', quiet=True)
                    nltk.download('punkt', quiet=True)
                    self.sentiment_analyzer = SentimentIntensityAnalyzer()
                except Exception as e:
                    logger.error(f"Failed to initialize sentiment analyzer: {e}")
    
    def analyze_lyrics(self, lyrics: str, theme: Optional[str] = None) -> LyricAnalysis:
        """
        歌詞を包括的に分析
        
        Args:
            lyrics: 分析する歌詞テキスト
            theme: テーマ（オプション、分類の参考に）
        
        Returns:
            LyricAnalysisオブジェクト
        """
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        # 品質評価
        quality = self.evaluate_quality(lyrics, lines)
        
        # 感情分析
        sentiment = self.analyze_sentiment(lyrics)
        
        # テーマ分類
        detected_theme = self.classify_theme(lyrics) if not theme else theme
        
        # スタイル分類
        style = self.classify_style(lyrics)
        
        # リズム分析
        rhythm = self.analyze_rhythm(lines)
        
        # 統計情報
        word_count = sum(len(line.split()) for line in lines)
        line_count = len(lines)
        avg_line_length = word_count / line_count if line_count > 0 else 0
        unique_words = len(set(word.lower() for line in lines for word in line.split()))
        vocabulary_richness = unique_words / word_count if word_count > 0 else 0
        
        return LyricAnalysis(
            quality=quality,
            sentiment=sentiment,
            theme=detected_theme,
            style=style,
            rhythm_pattern=rhythm,
            word_count=word_count,
            line_count=line_count,
            avg_line_length=avg_line_length,
            unique_words=unique_words,
            vocabulary_richness=vocabulary_richness
        )
    
    def evaluate_quality(self, lyrics: str, lines: List[str]) -> LyricQuality:
        """
        歌詞の品質を評価
        
        Args:
            lyrics: 歌詞テキスト
            lines: 歌詞の行リスト
        
        Returns:
            LyricQualityオブジェクト
        """
        # 韻のスコア
        rhyme_score = self._calculate_rhyme_score(lines)
        
        # リズムのスコア
        rhythm_score = self._calculate_rhythm_score(lines)
        
        # 一貫性スコア
        coherence_score = self._calculate_coherence_score(lyrics, lines)
        
        # 創造性スコア
        creativity_score = self._calculate_creativity_score(lyrics)
        
        # 長さの適切性
        length_score = self._calculate_length_score(lines)
        
        # 総合スコア（重み付き平均）
        overall_score = (
            rhyme_score * 0.25 +
            rhythm_score * 0.20 +
            coherence_score * 0.20 +
            creativity_score * 0.20 +
            length_score * 0.15
        )
        
        return LyricQuality(
            overall_score=overall_score,
            rhyme_score=rhyme_score,
            rhythm_score=rhythm_score,
            coherence_score=coherence_score,
            creativity_score=creativity_score,
            length_score=length_score,
            details={
                "rhyme_pairs": self._find_rhyme_pairs(lines),
                "rhythm_variance": self._calculate_rhythm_variance(lines),
                "repetition_ratio": self._calculate_repetition_ratio(lyrics)
            }
        )
    
    def _calculate_rhyme_score(self, lines: List[str]) -> float:
        """韻のスコアを計算"""
        if len(lines) < 2:
            return 0.0
        
        rhyme_pairs = self._find_rhyme_pairs(lines)
        total_pairs = len(lines) // 2
        
        if total_pairs == 0:
            return 0.0
        
        return min(1.0, len(rhyme_pairs) / total_pairs)
    
    def _find_rhyme_pairs(self, lines: List[str]) -> List[Tuple[int, int]]:
        """韻を踏んでいる行のペアを検出"""
        rhyme_pairs = []
        
        for i in range(len(lines) - 1):
            line1_words = lines[i].split()
            line2_words = lines[i + 1].split()
            
            if not line1_words or not line2_words:
                continue
            
            # 最後の単語の末尾を比較
            word1 = line1_words[-1].lower().rstrip('.,!?;:')
            word2 = line2_words[-1].lower().rstrip('.,!?;:')
            
            # 簡易的な韻判定（最後の2-3文字が一致）
            if len(word1) >= 2 and len(word2) >= 2:
                if word1[-2:] == word2[-2:] or word1[-3:] == word2[-3:]:
                    rhyme_pairs.append((i, i + 1))
        
        return rhyme_pairs
    
    def _calculate_rhythm_score(self, lines: List[str]) -> float:
        """リズムのスコアを計算（行の長さの一貫性）"""
        if len(lines) < 2:
            return 0.5
        
        line_lengths = [len(line.split()) for line in lines]
        avg_length = np.mean(line_lengths)
        
        if avg_length == 0:
            return 0.0
        
        # 標準偏差が小さいほどリズムが良い
        std_dev = np.std(line_lengths)
        # 正規化（0-1の範囲に）
        rhythm_score = 1.0 / (1.0 + std_dev / avg_length)
        
        return min(1.0, rhythm_score)
    
    def _calculate_coherence_score(self, lyrics: str, lines: List[str]) -> float:
        """一貫性スコアを計算"""
        if len(lines) < 2:
            return 0.5
        
        # 単語の重複度（同じ単語が繰り返される度合い）
        all_words = [word.lower() for line in lines for word in line.split()]
        unique_words = set(all_words)
        
        if len(all_words) == 0:
            return 0.0
        
        # 適度な重複は良い（0.3-0.7が理想）
        repetition_ratio = 1.0 - (len(unique_words) / len(all_words))
        coherence = 1.0 - abs(repetition_ratio - 0.5) * 2
        
        return max(0.0, min(1.0, coherence))
    
    def _calculate_creativity_score(self, lyrics: str) -> float:
        """創造性スコアを計算（語彙の多様性）"""
        words = lyrics.lower().split()
        if len(words) == 0:
            return 0.0
        
        unique_words = set(words)
        creativity = len(unique_words) / len(words)
        
        # 0.5-0.8が理想的な範囲
        if 0.5 <= creativity <= 0.8:
            return 1.0
        elif creativity < 0.5:
            return creativity * 2
        else:
            return 1.0 - (creativity - 0.8) * 2.5
    
    def _calculate_length_score(self, lines: List[str]) -> float:
        """長さの適切性スコア（8-32行が理想）"""
        line_count = len(lines)
        
        if 8 <= line_count <= 32:
            return 1.0
        elif line_count < 8:
            return line_count / 8.0
        else:
            # 32行を超える場合は減点
            return max(0.5, 1.0 - (line_count - 32) / 32.0)
    
    def _calculate_rhythm_variance(self, lines: List[str]) -> float:
        """リズムの分散を計算"""
        line_lengths = [len(line.split()) for line in lines]
        return float(np.var(line_lengths)) if line_lengths else 0.0
    
    def _calculate_repetition_ratio(self, lyrics: str) -> float:
        """繰り返し比率を計算"""
        words = lyrics.lower().split()
        if len(words) == 0:
            return 0.0
        unique_words = set(words)
        return 1.0 - (len(unique_words) / len(words))
    
    def analyze_sentiment(self, lyrics: str) -> LyricSentiment:
        """
        歌詞の感情を分析
        
        Args:
            lyrics: 歌詞テキスト
        
        Returns:
            LyricSentimentオブジェクト
        """
        if self.sentiment_analyzer:
            scores = self.sentiment_analyzer.polarity_scores(lyrics)
            dominant = "positive" if scores['compound'] > 0.1 else \
                      "negative" if scores['compound'] < -0.1 else "neutral"
            
            return LyricSentiment(
                positive=scores['pos'],
                negative=scores['neg'],
                neutral=scores['neu'],
                compound=scores['compound'],
                dominant_emotion=dominant
            )
        else:
            # フォールバック: 簡易的な感情分析
            positive_words = ['love', 'happy', 'joy', 'smile', 'beautiful', 'wonderful']
            negative_words = ['sad', 'cry', 'pain', 'hurt', 'lonely', 'hate']
            
            words = lyrics.lower().split()
            pos_count = sum(1 for w in words if any(pw in w for pw in positive_words))
            neg_count = sum(1 for w in words if any(nw in w for nw in negative_words))
            total = len(words)
            
            pos_score = pos_count / total if total > 0 else 0.0
            neg_score = neg_count / total if total > 0 else 0.0
            neu_score = 1.0 - pos_score - neg_score
            compound = pos_score - neg_score
            
            dominant = "positive" if compound > 0.1 else \
                      "negative" if compound < -0.1 else "neutral"
            
            return LyricSentiment(
                positive=pos_score,
                negative=neg_score,
                neutral=neu_score,
                compound=compound,
                dominant_emotion=dominant
            )
    
    def classify_theme(self, lyrics: str) -> str:
        """
        テーマを分類
        
        Args:
            lyrics: 歌詞テキスト
        
        Returns:
            テーマ名
        """
        themes = {
            'love': ['love', 'heart', 'kiss', 'baby', 'darling', 'sweet', 'romance'],
            'party': ['party', 'dance', 'night', 'club', 'fun', 'celebration', 'wild'],
            'sad': ['sad', 'cry', 'tears', 'lonely', 'pain', 'hurt', 'miss', 'gone'],
            'motivational': ['fight', 'win', 'strong', 'power', 'dream', 'believe', 'rise'],
            'life': ['life', 'time', 'world', 'day', 'way', 'road', 'journey']
        }
        
        lyrics_lower = lyrics.lower()
        theme_scores = {}
        
        for theme, keywords in themes.items():
            score = sum(1 for keyword in keywords if keyword in lyrics_lower)
            theme_scores[theme] = score
        
        if theme_scores:
            return max(theme_scores, key=theme_scores.get)
        return 'general'
    
    def classify_style(self, lyrics: str) -> str:
        """
        スタイルを分類
        
        Args:
            lyrics: 歌詞テキスト
        
        Returns:
            スタイル名
        """
        # 簡易的なスタイル分類
        lyrics_lower = lyrics.lower()
        
        # ラップの特徴: 短い行、繰り返し、スラング
        if any(word in lyrics_lower for word in ['yo', 'yeah', 'uh', 'ay', 'check']):
            return 'rap'
        
        # ポップの特徴: 長い行、感情的な表現
        avg_line_length = np.mean([len(line.split()) for line in lyrics.split('\n') if line.strip()])
        if avg_line_length > 8:
            return 'pop'
        
        # その他
        return 'rap'  # デフォルト
    
    def analyze_rhythm(self, lines: List[str]) -> Dict[str, any]:
        """
        リズムパターンを分析
        
        Args:
            lines: 歌詞の行リスト
        
        Returns:
            リズム分析結果
        """
        line_lengths = [len(line.split()) for line in lines]
        
        return {
            "avg_syllables_per_line": float(np.mean(line_lengths)) if line_lengths else 0.0,
            "std_syllables": float(np.std(line_lengths)) if line_lengths else 0.0,
            "min_syllables": int(min(line_lengths)) if line_lengths else 0,
            "max_syllables": int(max(line_lengths)) if line_lengths else 0,
            "rhythm_pattern": self._detect_rhythm_pattern(line_lengths)
        }
    
    def _detect_rhythm_pattern(self, line_lengths: List[int]) -> str:
        """リズムパターンを検出"""
        if len(line_lengths) < 4:
            return "irregular"
        
        # パターンの検出（簡易版）
        if all(4 <= length <= 8 for length in line_lengths):
            return "consistent"
        elif len(set(line_lengths)) <= 2:
            return "repetitive"
        else:
            return "varied"
    
    def compare_lyrics(self, lyrics1: str, lyrics2: str) -> float:
        """
        2つの歌詞の類似度を計算
        
        Args:
            lyrics1: 歌詞1
            lyrics2: 歌詞2
        
        Returns:
            類似度スコア（0-1）
        """
        if not SKLEARN_AVAILABLE:
            # 簡易的な類似度計算
            words1 = set(lyrics1.lower().split())
            words2 = set(lyrics2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        
        # TF-IDFベースの類似度計算
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        try:
            vectors = self.vectorizer.fit_transform([lyrics1, lyrics2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def suggest_improvements(self, analysis: LyricAnalysis) -> List[str]:
        """
        歌詞の改善提案を生成
        
        Args:
            analysis: 歌詞分析結果
        
        Returns:
            改善提案のリスト
        """
        suggestions = []
        
        if analysis.quality.rhyme_score < 0.5:
            suggestions.append("韻を踏む行を増やすと、よりリズミカルになります")
        
        if analysis.quality.rhythm_score < 0.5:
            suggestions.append("各行の長さを揃えると、リズムが安定します")
        
        if analysis.quality.coherence_score < 0.5:
            suggestions.append("テーマを統一し、一貫性のある歌詞にしましょう")
        
        if analysis.quality.creativity_score < 0.3:
            suggestions.append("語彙を増やし、より創造的な表現を試してみましょう")
        elif analysis.quality.creativity_score > 0.9:
            suggestions.append("適度な繰り返しを入れると、覚えやすい歌詞になります")
        
        if analysis.line_count < 8:
            suggestions.append("歌詞を8行以上にすると、より完成度が高まります")
        elif analysis.line_count > 40:
            suggestions.append("歌詞を32行程度にまとめると、より効果的です")
        
        if analysis.vocabulary_richness < 0.3:
            suggestions.append("同じ単語の繰り返しを減らし、語彙を豊かにしましょう")
        
        return suggestions


# グローバルインスタンス
_analyzer: Optional[LyricsMLAnalyzer] = None


def get_analyzer() -> LyricsMLAnalyzer:
    """グローバルアナライザーインスタンスを取得"""
    global _analyzer
    if _analyzer is None:
        _analyzer = LyricsMLAnalyzer()
    return _analyzer


def analyze_lyrics(lyrics: str, theme: Optional[str] = None) -> LyricAnalysis:
    """
    歌詞を分析（簡易関数）
    
    Args:
        lyrics: 歌詞テキスト
        theme: テーマ（オプション）
    
    Returns:
        LyricAnalysisオブジェクト
    """
    analyzer = get_analyzer()
    return analyzer.analyze_lyrics(lyrics, theme)

