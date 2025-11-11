import argparse
from pathlib import Path
from .generator import generate_song_lyrics, save_lyrics_to_file
from loguru import logger

def parse_arguments():
    parser = argparse.ArgumentParser(description="AI Rapper - Rule-based Song Generator")
    parser.add_argument("--theme", type=str, default="love",
                      help="Theme of the song (e.g., love, party, sad)")
    parser.add_argument("--style", type=str, default="rap",
                      help="Style of the song (e.g., rap, pop)")
    parser.add_argument("--output", type=Path, default="generated_song.txt",
                      help="Output file path for the lyrics")
    return parser.parse_args()

def main():
    logger.info("Starting AI Rapper...")
    args = parse_arguments()
    
    # Generate song
    logger.info(f"Generating {args.theme} song in {args.style} style...")
    song = generate_song_lyrics(theme=args.theme, style=args.style)
    
    # Save to file
    output_path = args.output
    save_lyrics_to_file(song, output_path)
    
    # Print success message
    logger.success(f"Successfully generated song: {song.title}")
    logger.info(f"BPM: {song.bpm}, Key: {song.key}")
    logger.info(f"Lyrics saved to: {output_path.absolute()}")

if __name__ == "__main__":
    main()
