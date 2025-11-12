import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
from pathlib import Path

from .gguf_loader import get_loader, generate_with_gguf

@dataclass
class Song:
    title: str
    lyrics: List[str]
    bpm: int
    key: str

def generate_song_lyrics(
    theme: str = "love",
    style: str = "rap",
    model: str = "yue",
    use_ai: bool = True
) -> Song:
    """
    Generate song lyrics using GGUF models (rinna or YuE) or fallback to rule-based.
    
    Args:
        theme: Theme of the song (e.g., "love", "party", "sad")
        style: Style of the song (e.g., "rap", "pop")
        model: Model to use ("yue" or "rinna")
        use_ai: Whether to use AI model (True) or rule-based (False)
    
    Returns:
        Song object with lyrics, title, BPM, and key
    """
    if use_ai:
        try:
            return _generate_with_ai(theme, style, model)
        except Exception as e:
            logger.warning(f"AI generation failed: {e}, falling back to rule-based")
            return _generate_rule_based(theme, style)
    else:
        return _generate_rule_based(theme, style)


def _generate_with_ai(theme: str, style: str, model: str) -> Song:
    """AIモデルを使用して歌詞を生成"""
    # プロンプトの構築
    if model == "rinna":
        # rinnaは日本語モデルなので日本語プロンプト
        prompt = f"""以下のテーマとスタイルでラップの歌詞を生成してください。

テーマ: {theme}
スタイル: {style}

歌詞:"""
    else:
        # YuEは英語モデルなので英語プロンプト
        prompt = f"""Generate rap lyrics with the following theme and style.

Theme: {theme}
Style: {style}

Lyrics:"""
    
    logger.info(f"Generating lyrics with {model} model...")
    
    # GGUFモデルで生成
    generated_text = generate_with_gguf(
        prompt=prompt,
        model_name=model,
        max_tokens=512,
        temperature=0.8,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=["\n\n\n", "---", "==="] if model == "yue" else ["\n\n\n", "---", "==="]
    )
    
    # 生成されたテキストから歌詞を抽出
    lyrics_lines = _extract_lyrics_from_text(generated_text, model)
    
    # 歌詞が短すぎる場合は補完
    if len(lyrics_lines) < 8:
        logger.warning("Generated lyrics too short, supplementing...")
        additional = _generate_rule_based(theme, style)
        lyrics_lines.extend(additional.lyrics[:8])
    
    return Song(
        title=f"{theme.capitalize()} Song",
        lyrics=lyrics_lines,
        bpm=random.randint(80, 140) if style == "rap" else random.randint(70, 120),
        key=random.choice(["C", "D", "E", "F", "G", "A", "B", "Am", "Dm", "Em"])
    )


def _extract_lyrics_from_text(text: str, model: str) -> List[str]:
    """生成されたテキストから歌詞行を抽出"""
    lines = []
    
    # テキストを行に分割
    for line in text.split("\n"):
        line = line.strip()
        # 空行やプロンプト部分をスキップ
        if not line or line.startswith("テーマ") or line.startswith("Theme") or line.startswith("スタイル") or line.startswith("Style"):
            continue
        # 歌詞行として追加
        if len(line) > 3:  # 短すぎる行はスキップ
            lines.append(line)
    
    # 最低限の行数がない場合は空行を追加して構造化
    if len(lines) < 4:
        lines = lines * 2  # 繰り返し
    
    # 4行ごとに空行を挿入（verse区切り）
    formatted_lines = []
    for i, line in enumerate(lines):
        formatted_lines.append(line)
        if (i + 1) % 4 == 0 and i < len(lines) - 1:
            formatted_lines.append("")
    
    return formatted_lines[:32]  # 最大32行


def _generate_rule_based(theme: str, style: str) -> Song:
    """ルールベースの歌詞生成（フォールバック）"""
    # Basic word banks
    themes = {
        "love": ["heart", "love", "baby", "kiss", "hold", "touch", "feel"],
        "party": ["dance", "move", "night", "club", "fun", "jump", "wild"],
        "sad": ["tears", "cry", "alone", "pain", "hurt", "miss", "gone"]
    }
    
    templates = {
        "rap": [
            "Yo, {line1} {rhyme1}",
            "Listen up, {line2} {rhyme2}",
            "{line3} {rhyme3}, that's a fact",
            "{line4} {rhyme4}, no lookin' back"
        ],
        "pop": [
            "Oh, {line1} {rhyme1}",
            "{line2} {rhyme2}, can't you see?",
            "{line3} {rhyme3}, it's you and me",
            "{line4} {rhyme4}, wild and free"
        ]
    }
    
    # Select words based on theme
    word_bank = themes.get(theme.lower(), themes["love"])
    template = templates.get(style.lower(), templates["rap"])
    
    # Generate rhyming pairs
    def get_rhyme_pair():
        word1 = random.choice(word_bank)
        # Simple rhyming (in a real app, you'd use a proper rhyming dictionary)
        if word1.endswith("e"):
            rhyme = word1 + "e"
        else:
            rhyme = word1 + "ee"
        return word1, rhyme
    
    # Generate lyrics
    lyrics = []
    for _ in range(4):  # 4 verses
        word1, rhyme1 = get_rhyme_pair()
        word2, rhyme2 = get_rhyme_pair()
        
        verse = [
            t.format(
                line1=random.choice(word_bank),
                rhyme1=rhyme1,
                line2=random.choice(word_bank),
                rhyme2=rhyme2,
                line3=random.choice(word_bank),
                rhyme3=rhyme1,  # Reuse rhymes for structure
                line4=random.choice(word_bank),
                rhyme4=rhyme2
            )
            for t in template
        ]
        lyrics.extend(verse)
        lyrics.append("")  # Empty line between verses
    
    return Song(
        title=f"{theme.capitalize()} Song",
        lyrics=lyrics,
        bpm=random.randint(80, 120),
        key=random.choice(["C", "D", "E", "F", "G", "A", "B"])
    )

def save_lyrics_to_file(song: Song, filename: str = "lyrics.txt"):
    """Save the generated lyrics to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{song.title}\n")
        f.write(f"BPM: {song.bpm}, Key: {song.key}\n\n")
        f.write("\n".join(song.lyrics))
    logger.info(f"Lyrics saved to {filename}")

if __name__ == "__main__":
    # Example usage
    song = generate_song_lyrics(theme="love", style="rap")
    save_lyrics_to_file(song, "generated_song.txt")
    print("\n".join(song.lyrics))
