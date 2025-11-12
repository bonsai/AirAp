"""
ML分析機能のテスト
"""
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.lyrics_ml import analyze_lyrics, get_analyzer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("ML analysis not available")

def test_lyrics_analysis():
    """歌詞分析のテスト"""
    if not ML_AVAILABLE:
        print("⚠️  ML analysis not available, skipping test")
        return
    
    print("Testing lyrics analysis...")
    
    sample_lyrics = """
    Yo, this is my rap
    Listen up, don't look back
    Love is in the air
    Everywhere I stare
    """
    
    analysis = analyze_lyrics(sample_lyrics, theme="love")
    
    assert analysis.quality is not None
    assert analysis.sentiment is not None
    assert analysis.theme is not None
    assert analysis.style is not None
    
    print(f"✅ Analysis completed")
    print(f"   Quality score: {analysis.quality.overall_score:.2f}")
    print(f"   Rhyme score: {analysis.quality.rhyme_score:.2f}")
    print(f"   Sentiment: {analysis.sentiment.dominant_emotion}")
    print(f"   Theme: {analysis.theme}")
    print(f"   Style: {analysis.style}")
    print()

def test_quality_evaluation():
    """品質評価のテスト"""
    if not ML_AVAILABLE:
        print("⚠️  ML analysis not available, skipping test")
        return
    
    print("Testing quality evaluation...")
    
    analyzer = get_analyzer()
    
    good_lyrics = """
    Love is in the air
    Everywhere I stare
    You are so fair
    I really care
    """
    
    quality = analyzer.evaluate_quality(good_lyrics, good_lyrics.split('\n'))
    
    assert 0 <= quality.overall_score <= 1
    assert 0 <= quality.rhyme_score <= 1
    assert 0 <= quality.rhythm_score <= 1
    
    print(f"✅ Quality evaluation completed")
    print(f"   Overall: {quality.overall_score:.2f}")
    print(f"   Rhyme: {quality.rhyme_score:.2f}")
    print(f"   Rhythm: {quality.rhythm_score:.2f}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("ML Analysis Tests")
    print("=" * 50)
    print()
    
    test_lyrics_analysis()
    test_quality_evaluation()
    
    print("=" * 50)
    print("ML analysis tests completed!")
    print("=" * 50)

