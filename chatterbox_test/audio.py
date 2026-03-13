from pathlib import Path

import torchaudio
from chatterbox.tts import ChatterboxTTS


def run_emotion_tone_clone_test() -> None:
    base_dir = Path(__file__).resolve().parent
    reference_audio = base_dir / "male_reference.wav"

    if not reference_audio.exists():
        raise FileNotFoundError(f"Reference audio not found: {reference_audio}")

    text = "Hello Sajer, this is your AI speaking with the same tone and emotion."
    model = ChatterboxTTS.from_pretrained(device="cpu")

    # Baseline TTS without voice/tone cloning.
    neutral_wav = model.generate(text)
    neutral_out = base_dir / "output_neutral.wav"
    torchaudio.save(str(neutral_out), neutral_wav, model.sr)

    # Cloning from reference audio to transfer speaker style and prosody.
    cloned_wav = model.generate(
        text,
        audio_prompt_path=str(reference_audio),
        exaggeration=0.7,
        cfg_weight=0.8,
    )
    cloned_out = base_dir / "output_cloned.wav"
    torchaudio.save(str(cloned_out), cloned_wav, model.sr)

    print(f"Saved baseline audio: {neutral_out}")
    print(f"Saved cloned audio:   {cloned_out}")


if __name__ == "__main__":
    run_emotion_tone_clone_test()
