import random
from typing import List, Dict
import random
from dataclasses import dataclass
from loguru import logger

@dataclass
class Song:
    title: str
    lyrics: List[str]
    bpm: int
    key: str

def generate_song_lyrics(theme: str = "love", style: str = "rap") -> Song:
    """
    Generate song lyrics based on theme and style.
    This is a simple rule-based implementation.
    """
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
