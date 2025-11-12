"""
音楽生成モジュール
歌詞からMIDIを生成し、MP3に変換
"""
from pathlib import Path
from typing import Optional
import numpy as np
from loguru import logger
import subprocess
import tempfile
import os

try:
    from music21 import stream, note, chord, tempo, key, meter
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    logger.warning("music21 not available, using fallback method")

try:
    from midiutil import MIDIFile
    MIDIUTIL_AVAILABLE = True
except ImportError:
    MIDIUTIL_AVAILABLE = False
    logger.warning("midiutil not available, using fallback method")

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available, using fallback method")


def compose_music_from_lyrics(
    lyrics: str,
    output_path: Path,
    bpm: int = 120,
    key: str = "C"
) -> Path:
    """
    歌詞から音楽を生成してMP3ファイルとして保存
    
    Args:
        lyrics: 歌詞テキスト
        output_path: 出力MP3ファイルのパス
        bpm: テンポ（BPM）
        key: キー（例: "C", "D", "Am"）
    
    Returns:
        生成されたMP3ファイルのパス
    """
    logger.info(f"Composing music: BPM={bpm}, Key={key}")
    
    # 歌詞を解析してメロディーを生成
    melody_notes = generate_melody_from_lyrics(lyrics, bpm, key)
    
    # MIDIファイルを生成
    midi_path = output_path.with_suffix('.mid')
    create_midi_file(melody_notes, midi_path, bpm, key)
    
    # MIDIをMP3に変換
    convert_midi_to_mp3(midi_path, output_path)
    
    # 一時MIDIファイルを削除
    if midi_path.exists():
        midi_path.unlink()
    
    logger.success(f"Music composed and saved to: {output_path}")
    return output_path


def generate_melody_from_lyrics(
    lyrics: str,
    bpm: int = 120,
    key: str = "C"
) -> list:
    """
    歌詞からメロディーノートを生成
    
    Returns:
        ノートのリスト [(pitch, duration, start_time), ...]
    """
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    
    # キーから基本スケールを決定
    scale_notes = get_scale_notes(key)
    
    melody = []
    current_time = 0.0
    note_duration = 60.0 / bpm  # 四分音符の長さ（秒）
    
    for line in lines:
        words = line.split()
        notes_per_line = max(4, len(words))  # 最低4ノート
        
        for i in range(notes_per_line):
            # 単純なメロディーパターン生成
            note_index = i % len(scale_notes)
            pitch = scale_notes[note_index]
            
            # リズムバリエーション
            if i % 4 == 0:
                duration = note_duration * 2  # 二分音符
            elif i % 2 == 0:
                duration = note_duration  # 四分音符
            else:
                duration = note_duration * 0.5  # 八分音符
            
            melody.append({
                'pitch': pitch,
                'duration': duration,
                'start_time': current_time
            })
            
            current_time += duration
        
        # 行の間に休符を追加
        current_time += note_duration * 0.5
    
    return melody


def get_scale_notes(key: str) -> list:
    """
    キーからスケールノートを取得（MIDIノート番号）
    """
    # メジャースケールのパターン（半音単位）
    major_pattern = [0, 2, 4, 5, 7, 9, 11]
    
    # キー名から基本ノートを取得
    key_map = {
        'C': 60, 'C#': 61, 'Db': 61, 'D': 62, 'D#': 63, 'Eb': 63,
        'E': 64, 'F': 65, 'F#': 66, 'Gb': 66, 'G': 67, 'G#': 68,
        'Ab': 68, 'A': 69, 'A#': 70, 'Bb': 70, 'B': 71
    }
    
    # マイナーキーの処理
    is_minor = key.endswith('m') or key.endswith('min')
    base_key = key.rstrip('m').rstrip('min')
    
    base_note = key_map.get(base_key, 60)  # デフォルトはC
    
    if is_minor:
        # マイナースケール（ナチュラルマイナー）
        minor_pattern = [0, 2, 3, 5, 7, 8, 10]
        return [base_note + offset for offset in minor_pattern]
    else:
        # メジャースケール
        return [base_note + offset for offset in major_pattern]


def create_midi_file(
    melody: list,
    output_path: Path,
    bpm: int = 120,
    key: str = "C"
):
    """
    MIDIファイルを作成
    """
    if MUSIC21_AVAILABLE:
        create_midi_with_music21(melody, output_path, bpm, key)
    elif MIDIUTIL_AVAILABLE:
        create_midi_with_midiutil(melody, output_path, bpm)
    else:
        # フォールバック: シンプルなMIDI生成
        create_simple_midi(melody, output_path, bpm)


def create_midi_with_music21(
    melody: list,
    output_path: Path,
    bpm: int,
    key: str
):
    """music21を使用してMIDIを作成"""
    try:
        s = stream.Stream()
        s.insert(0, tempo.MetronomeMark(number=bpm))
        s.insert(0, key.Key(key))
        s.insert(0, meter.TimeSignature('4/4'))
        
        for note_data in melody:
            n = note.Note(note_data['pitch'])
            n.duration.quarterLength = note_data['duration'] / (60.0 / bpm / 4)
            s.insert(note_data['start_time'] / (60.0 / bpm / 4), n)
        
        s.write('midi', fp=str(output_path))
        logger.info(f"MIDI file created with music21: {output_path}")
    except Exception as e:
        logger.error(f"Error creating MIDI with music21: {e}")
        create_simple_midi(melody, output_path, bpm)


def create_midi_with_midiutil(
    melody: list,
    output_path: Path,
    bpm: int
):
    """midiutilを使用してMIDIを作成"""
    try:
        midi = MIDIFile(1)
        track = 0
        time = 0
        
        midi.addTrackName(track, time, "AI Rapper")
        midi.addTempo(track, time, bpm)
        
        for note_data in melody:
            pitch = note_data['pitch']
            duration = note_data['duration'] * bpm / 60.0  # 秒を拍に変換
            start_time = note_data['start_time'] * bpm / 60.0
            
            midi.addNote(
                track, 0, pitch, start_time, duration, 100
            )
        
        with open(output_path, 'wb') as f:
            midi.writeFile(f)
        
        logger.info(f"MIDI file created with midiutil: {output_path}")
    except Exception as e:
        logger.error(f"Error creating MIDI with midiutil: {e}")
        create_simple_midi(melody, output_path, bpm)


def create_simple_midi(
    melody: list,
    output_path: Path,
    bpm: int
):
    """シンプルなMIDIファイル作成（フォールバック）"""
    logger.warning("Using simple MIDI creation (fallback)")
    
    # midoライブラリを使用したフォールバック実装
    try:
        import mido
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # テンポ設定
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        # ノートを追加
        current_tick = 0
        ticks_per_beat = mid.ticks_per_beat
        
        for note_data in melody:
            # 開始時間をティックに変換
            start_tick = int(note_data['start_time'] * bpm / 60.0 * ticks_per_beat)
            duration_ticks = int(note_data['duration'] * bpm / 60.0 * ticks_per_beat)
            
            # 待機時間を計算
            wait_ticks = start_tick - current_tick
            if wait_ticks > 0:
                track.append(mido.Message('note_on', note=note_data['pitch'], velocity=64, time=wait_ticks))
            else:
                track.append(mido.Message('note_on', note=note_data['pitch'], velocity=64, time=0))
            
            # ノートオフ
            track.append(mido.Message('note_off', note=note_data['pitch'], velocity=64, time=duration_ticks))
            current_tick = start_tick + duration_ticks
        
        mid.save(str(output_path))
        logger.info(f"MIDI file created with mido: {output_path}")
    except ImportError:
        logger.error("No MIDI library available (music21, midiutil, or mido required)")
        raise RuntimeError("MIDI creation requires music21, midiutil, or mido")
    except Exception as e:
        logger.error(f"Error creating MIDI with mido: {e}")
        raise RuntimeError(f"MIDI creation failed: {e}")


def convert_midi_to_mp3(midi_path: Path, mp3_path: Path):
    """
    MIDIファイルをMP3に変換
    """
    logger.info(f"Converting MIDI to MP3: {midi_path} -> {mp3_path}")
    
    # 方法1: fluidsynth + ffmpegを使用
    if convert_with_fluidsynth(midi_path, mp3_path):
        return
    
    # 方法2: timidity + ffmpegを使用
    if convert_with_timidity(midi_path, mp3_path):
        return
    
    # 方法3: 直接ffmpeg（MIDIサポートがある場合）
    if convert_with_ffmpeg_direct(midi_path, mp3_path):
        return
    
    # フォールバック: エラー
    raise RuntimeError(
        "MIDI to MP3 conversion failed. "
        "Please ensure fluidsynth or timidity is installed."
    )


def convert_with_fluidsynth(midi_path: Path, mp3_path: Path) -> bool:
    """fluidsynthを使用してMIDIをMP3に変換"""
    try:
        # 一時WAVファイル
        wav_path = mp3_path.with_suffix('.wav')
        
        # fluidsynthでMIDIをWAVに変換
        # デフォルトのサウンドフォントを使用（システムにインストールされている場合）
        soundfont = None
        for path in [
            "/usr/share/sounds/sf2/FluidR3_GM.sf2",
            "/usr/share/soundfonts/FluidR3_GM.sf2",
            "/usr/local/share/soundfonts/FluidR3_GM.sf2",
            "/usr/share/fluidsynth/default.sf2"
        ]:
            if os.path.exists(path):
                soundfont = path
                break
        
        if soundfont:
            # fluidsynthコマンド（-Fでファイル出力、-niで非対話モード）
            cmd = [
                "fluidsynth", "-ni", "-F", str(wav_path),
                soundfont, str(midi_path)
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 0:
                # WAVをMP3に変換
                convert_wav_to_mp3(wav_path, mp3_path)
                wav_path.unlink()  # 一時ファイル削除
                return True
            else:
                logger.debug(f"fluidsynth failed: returncode={result.returncode}, stderr={result.stderr}")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"fluidsynth conversion failed: {e}")
    
    return False


def convert_with_timidity(midi_path: Path, mp3_path: Path) -> bool:
    """timidityを使用してMIDIをMP3に変換"""
    try:
        wav_path = mp3_path.with_suffix('.wav')
        
        cmd = ["timidity", str(midi_path), "-Ow", "-o", str(wav_path)]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0 and wav_path.exists():
            convert_wav_to_mp3(wav_path, mp3_path)
            wav_path.unlink()
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"timidity conversion failed: {e}")
    
    return False


def convert_with_ffmpeg_direct(midi_path: Path, mp3_path: Path) -> bool:
    """ffmpegで直接MIDIをMP3に変換（MIDIサポートがある場合）"""
    try:
        cmd = [
            "ffmpeg", "-i", str(midi_path),
            "-y", str(mp3_path)
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0 and mp3_path.exists():
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"ffmpeg direct conversion failed: {e}")
    
    return False


def convert_wav_to_mp3(wav_path: Path, mp3_path: Path):
    """WAVファイルをMP3に変換"""
    try:
        cmd = [
            "ffmpeg", "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            "-y", str(mp3_path)
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error converting WAV to MP3: {e}")
        raise

