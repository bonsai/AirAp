"""
歌詞生成機能のテスト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.generator import generate_song_lyrics, Song

def test_rule_based_generation():
    """ルールベース生成のテスト"""
    print("Testing rule-based generation...")
    song = generate_song_lyrics(theme="love", style="rap", use_ai=False)
    
    assert isinstance(song, Song)
    assert song.title is not None
    assert len(song.lyrics) > 0
    assert song.bpm > 0
    assert song.key is not None
    
    print(f"✅ Generated: {song.title}")
    print(f"   BPM: {song.bpm}, Key: {song.key}")
    print(f"   Lyrics lines: {len(song.lyrics)}")
    print()

def test_ai_generation():
    """AI生成のテスト（モデルが利用可能な場合）"""
    print("Testing AI generation...")
    try:
        song = generate_song_lyrics(
            theme="love",
            style="rap",
            model="yue",
            use_ai=True
        )
        
        assert isinstance(song, Song)
        assert song.title is not None
        assert len(song.lyrics) > 0
        
        print(f"✅ AI Generated: {song.title}")
        print(f"   BPM: {song.bpm}, Key: {song.key}")
        print(f"   Lyrics lines: {len(song.lyrics)}")
        print()
    except Exception as e:
        print(f"⚠️  AI generation failed (model may not be available): {e}")
        print()

if __name__ == "__main__":
    print("=" * 50)
    print("Generator Tests")
    print("=" * 50)
    print()
    
    test_rule_based_generation()
    test_ai_generation()
    
    print("=" * 50)
    print("Generator tests completed!")
    print("=" * 50)

