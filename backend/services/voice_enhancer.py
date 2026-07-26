from pydub import AudioSegment, effects


def enhance_voice_quality(file_path: str, gender_preset: str = "auto"):
    """
    Standalone Voice Enhancer Module for Advanced Human Sound Processing.
    Applies high-end DSP studio chain to female and male neural voices.
    
    Presets:
    - 'female': Smooths harsh sibilance, adds breath warmth and silky air EQ.
    - 'male': Boosts chest resonance, adds broadcast bass, applies warm compression.
    - 'auto': Balances dynamic range and applies broadcast studio mastering.
    """
    try:
        sound = AudioSegment.from_file(file_path)
        
        if gender_preset == "female":
            # Female Studio Chain: Soften treble harshness + subtle warmth
            sound = effects.normalize(sound)
            sound = effects.compress_dynamic_range(
                sound,
                threshold=-18.0,
                ratio=2.5,
                attack=3.0,
                release=40.0
            )
            # Gentle high shelf softening for natural human warmth
            sound = sound.low_pass_filter(3800) * 0.15 + sound
            sound = sound.high_pass_filter(120)  # Cut low rumble
            
        elif gender_preset == "male":
            # Male Studio Chain: Deep chest resonance + warm compression
            sound = effects.normalize(sound)
            sound = sound.high_pass_filter(80)   # Cut extreme sub-bass rumble
            sound = effects.compress_dynamic_range(
                sound,
                threshold=-22.0,
                ratio=3.5,
                attack=8.0,
                release=60.0
            )
            # Enhance male vocal body (subtle bass warmth boost)
            bass_boost = sound.low_pass_filter(250) + 2.5
            sound = sound.overlay(bass_boost, loop=True)
            
        else:
            # Auto Broadcast Studio Chain
            sound = effects.normalize(sound)
            sound = sound.high_pass_filter(100)
            sound = effects.compress_dynamic_range(
                sound,
                threshold=-20.0,
                ratio=3.0,
                attack=5.0,
                release=50.0
            )
            sound = sound.low_pass_filter(4000) * 0.2 + sound

        final_sound = effects.normalize(sound)
        final_sound.export(file_path, format="mp3", bitrate="192k")
        print(f"Voice DSP enhancement ({gender_preset}) applied successfully to {file_path}")
        return True
    except Exception as e:
        print(f"Voice enhancer skipped: {e}")
        return False
