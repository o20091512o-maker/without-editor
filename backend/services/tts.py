import edge_tts
import asyncio
import os
import re
from pydub import AudioSegment, effects


def is_arabic(text: str) -> bool:
    """Check if string contains any Arabic characters."""
    return any('\u0600' <= char <= '\u06ff' for char in text)


def enhance_audio(file_path: str):
    """
    Apply DSP audio post-processing:
    - Normalization
    - Dynamic Range Compression
    - Low-pass filter for warmth
    """
    try:
        sound = AudioSegment.from_file(file_path)
        sound = effects.normalize(sound)
        sound = effects.compress_dynamic_range(
            sound,
            threshold=-20.0,
            ratio=3.0,
            attack=5.0,
            release=50.0
        )
        sound = sound.low_pass_filter(3500) * 0.2 + sound
        sound = effects.normalize(sound)
        sound.export(file_path, format="mp3", bitrate="192k")
    except Exception as e:
        print(f"Audio enhancement skipped: {e}")


def split_bilingual_text(text: str):
    """
    Split mixed text into contiguous segments of Arabic and English/Latin text.
    """
    tokens = re.split(r'([\u0600-\u06FF\s]+|[a-zA-Z0-9\s.,!?-]+)', text)
    segments = []
    for token in tokens:
        if not token or not token.strip():
            continue
        lang = "ar" if is_arabic(token) else "en"
        if segments and segments[-1][0] == lang:
            segments[-1] = (lang, segments[-1][1] + token)
        else:
            segments.append((lang, token))
    return segments if segments else [("ar" if is_arabic(text) else "en", text)]


async def _generate_segment(text: str, voice: str, temp_path: str):
    # pitch="-2Hz" and rate="-4%" produces deep, natural broadcast human sound
    communicate = edge_tts.Communicate(text, voice, pitch="-2Hz", rate="-4%")
    await communicate.save(temp_path)


def generate_audio(text: str, output_path: str):
    """
    Generate audio supporting mixed Arabic and English in the same text using fast Edge-TTS.
    """
    segments = split_bilingual_text(text)
    
    if len(segments) <= 1:
        voice = "ar-SA-ZariyahNeural" if is_arabic(text) else "en-US-ChristopherNeural"
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_generate_segment(text, voice, output_path))
        finally:
            loop.close()
    else:
        temp_files = []
        combined_audio = AudioSegment.empty()
        
        loop = asyncio.new_event_loop()
        try:
            for idx, (lang, seg_text) in enumerate(segments):
                voice = "ar-SA-ZariyahNeural" if lang == "ar" else "en-US-ChristopherNeural"
                seg_file = f"{output_path}_seg_{idx}.mp3"
                temp_files.append(seg_file)
                loop.run_until_complete(_generate_segment(seg_text, voice, seg_file))
                
                if os.path.exists(seg_file):
                    segment_audio = AudioSegment.from_file(seg_file)
                    combined_audio += segment_audio
                    
            combined_audio.export(output_path, format="mp3", bitrate="192k")
        finally:
            loop.close()
            for tf in temp_files:
                if os.path.exists(tf):
                    try:
                        os.remove(tf)
                    except Exception:
                        pass
        
    enhance_audio(output_path)
