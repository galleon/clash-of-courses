#!/usr/bin/env -S uv run --with openai --with pydub --with python-dotenv --with requests
"""
Generate a single merged soundtrack from an external info text file of timestamped sections.

Input file format (UTF-8):
    [M:SS]
    Narration text line 1
    Narration text line 2
    ...
    <blank line>
    [M:SS]
    ...

You may also add a **final [M:SS] marker with no narration** to indicate the movie's
target duration. If present, the script pads trailing silence to reach that length.
If absent, the soundtrack ends naturally where the last narrated section ends.

Outputs:
    - build/sections/section_{idx}_{MM-SS}.mp3  (per-section raw TTS, only for narrated sections)
    - build/final_soundtrack.mp3                 (merged + aligned to timestamps)

Requires:
    ffmpeg installed and on PATH for pydub

Env:
    OPENAI_API_KEY   (for OpenAI provider)
    11LABS_KEY       (for ElevenLabs provider)
    ELEVEN_VOICE_ID  (optional default voice id for ElevenLabs)
"""

import os
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

from dotenv import load_dotenv
from pydub import AudioSegment
import requests
import openai

# --- Load env ---
load_dotenv()

# --- Paths / constants ---
INFO_FILE_DEFAULT = Path("video_info.txt")
BUILD_DIR = Path("build")
SECTIONS_DIR = BUILD_DIR / "sections"
FINAL_MP3 = BUILD_DIR / "final_soundtrack.mp3"

# OpenAI defaults
DEFAULT_OAI_MODEL = "gpt-4o-mini-tts"
DEFAULT_OAI_VOICE = "alloy"

# ElevenLabs defaults
# A French-accented voice for English text (premade): "Charlotte"
# You can override via --eleven-voice-id or ELEVEN_VOICE_ID in env
DEFAULT_ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "XB0fDUnXU5powFXDhCwa")
DEFAULT_ELEVEN_MODEL_ID = "eleven_multilingual_v2"

Section = Tuple[float, str]  # (start_seconds, narration_text)


def parse_info(text: str) -> Tuple[List[Section], Optional[float]]:
    """
    Parse [M:SS] sections. Returns:
      - sections: list of narrated sections (start_seconds, narration)
      - final_len_s: optional final movie length from a trailing empty section
    """
    pattern = r"\[(\d+:\d{2})\]\s*\n(.*?)(?=\n\[\d+:\d{2}\]|\Z)"
    matches = re.findall(pattern, text, flags=re.S)

    narrated: List[Section] = []
    final_len_s: Optional[float] = None

    for ts, body in matches:
        m, s = ts.split(":")
        start = int(m) * 60 + int(s)
        block = body.strip()
        if block:
            narrated.append((float(start), block))

    # If the very last matched block was empty, treat it as the final length marker
    if matches:
        last_ts, last_body = matches[-1]
        if not last_body.strip():
            m, s = last_ts.split(":")
            final_len_s = int(m) * 60 + int(s)

    # Ensure sections are sorted and timestamps non-decreasing
    narrated.sort(key=lambda x: x[0])
    prev = -1.0
    for start, _ in narrated:
        if start < prev:
            raise SystemExit("Timestamps must be non-decreasing.")
        prev = start

    return narrated, final_len_s


def ensure_dirs():
    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------
# TTS Providers
# -----------------------
def tts_openai(text: str, model: str, voice: str) -> bytes:
    """Synthesize MP3 bytes using OpenAI TTS."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it to your .env file or environment."
        )
    resp = openai.audio.speech.create(model=model, voice=voice, input=text)
    return resp.content


def tts_elevenlabs(text: str, voice_id: str, model_id: str) -> bytes:
    """Synthesize MP3 bytes using ElevenLabs Text-to-Speech REST API."""
    api_key = os.getenv("11LABS_KEY")
    if not api_key:
        raise RuntimeError(
            "11LABS_KEY is not set. Please add it to your .env file or environment."
        )

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs TTS failed [{r.status_code}]: {r.text[:500]}")
    return r.content


def synthesize_tts_mp3(
    text: str,
    out_path: Path,
    provider: str,
    oai_model: str,
    oai_voice: str,
    el_voice_id: str,
    el_model_id: str,
) -> None:
    """Dispatch to chosen provider and write MP3 to out_path."""
    if provider == "openai":
        audio_bytes = tts_openai(text, model=oai_model, voice=oai_voice)
    elif provider == "elevenlabs":
        audio_bytes = tts_elevenlabs(text, voice_id=el_voice_id, model_id=el_model_id)
    else:
        raise ValueError(f"Unknown TTS provider: {provider}")

    out_path.write_bytes(audio_bytes)


def mmss(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(round(seconds - m * 60))
    return f"{m:01d}-{s:02d}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate merged soundtrack from timestamped narration."
    )
    parser.add_argument(
        "--info-file",
        type=Path,
        default=INFO_FILE_DEFAULT,
        help="Path to external info text file.",
    )
    parser.add_argument(
        "--tts-provider",
        choices=["openai", "elevenlabs"],
        default="openai",
        help="Choose TTS backend.",
    )
    parser.add_argument(
        "--openai-model",
        default=DEFAULT_OAI_MODEL,
        help="OpenAI TTS model (default: gpt-4o-mini-tts).",
    )
    parser.add_argument(
        "--openai-voice",
        default=DEFAULT_OAI_VOICE,
        help="OpenAI TTS voice (default: alloy).",
    )
    parser.add_argument(
        "--eleven-voice-id",
        default=DEFAULT_ELEVEN_VOICE_ID,
        help="ElevenLabs voice_id (default: Charlotte).",
    )
    parser.add_argument(
        "--eleven-model-id",
        default=DEFAULT_ELEVEN_MODEL_ID,
        help="ElevenLabs model_id (default: eleven_multilingual_v2).",
    )
    args = parser.parse_args()

    if not args.info_file.exists():
        raise SystemExit(f"Info file not found: {args.info_file}")

    ensure_dirs()
    text = args.info_file.read_text(encoding="utf-8")
    sections, final_len_s = parse_info(text)
    if not sections and final_len_s is None:
        raise SystemExit(
            "No narrated sections found and no final length marker provided."
        )

    # Step 1: TTS each narrated section
    rendered = []
    for idx, (start, narration) in enumerate(sections, 1):
        out = SECTIONS_DIR / f"section_{idx}_{mmss(start)}.mp3"
        print(
            f"[TTS:{args.tts_provider}] {idx}/{len(sections)} @ {start:.1f}s -> {out.name}"
        )
        synthesize_tts_mp3(
            narration,
            out_path=out,
            provider=args.tts_provider,
            oai_model=args.openai_model,
            oai_voice=args.openai_voice,
            el_voice_id=args.eleven_voice_id,
            el_model_id=args.eleven_model_id,
        )
        rendered.append((start, out))

    # Step 2: Merge into a single track, aligned to timestamps
    print("[MERGE] Assembling timeline ...")
    timeline = AudioSegment.silent(duration=0)  # ms
    cursor_ms = 0

    for start_s, audio_path in rendered:
        seg = AudioSegment.from_file(audio_path)
        start_ms = int(round(start_s * 1000))
        if start_ms > cursor_ms:
            timeline += AudioSegment.silent(duration=(start_ms - cursor_ms))
            cursor_ms = start_ms
        timeline += seg
        cursor_ms += len(seg)

    # Step 3: Optional end padding from final [M:SS] with no narration
    if final_len_s is not None:
        target_ms = int(round(final_len_s * 1000))
        if cursor_ms < target_ms:
            timeline += AudioSegment.silent(duration=(target_ms - cursor_ms))
            cursor_ms = target_ms
        print(f"[MERGE] Final duration aligned to marker: {final_len_s:.2f}s")
    else:
        print(f"[MERGE] Final duration = {cursor_ms / 1000:.2f}s (natural end)")

    # Export
    FINAL_MP3.parent.mkdir(parents=True, exist_ok=True)
    timeline.export(FINAL_MP3, format="mp3")
    print(f"\n✅ Done. Wrote {FINAL_MP3} | duration ≈ {cursor_ms / 1000:.2f}s")


if __name__ == "__main__":
    main()
