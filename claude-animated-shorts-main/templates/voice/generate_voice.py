#!/usr/bin/env python3
"""
Auto-generator untuk templates/voice/voice.wav (48 kHz) dan templates/voice/words.json
Menggunakan edge-tts + ffmpeg (jika tersedia) atau fallback synthesizer 48 kHz agar mix.py langsung jalan.
"""
import os
import json
import subprocess
import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(HERE, exist_ok=True)
WAV_PATH = os.path.join(HERE, "voice.wav")
WORDS_PATH = os.path.join(HERE, "words.json")

SCRIPT_LINES = [
    "Seventy-four soldiers knocked down an iron bridge just by walking across it.",
    "It's 1831, and the brand new bridge over the river is the pride of the whole town.",
    "The men are marching home four across, every boot hitting the planks at the exact same moment.",
    "Halfway over, the bridge starts bouncing under their feet.",
    "A normal person would slow down, but these guys think it's hilarious.",
    "Somebody starts whistling a marching tune, and the whole column stomps along to it, a little harder every step.",
    "The bounce gets bigger, the chains start groaning, and nobody wants to be the one who breaks step.",
    "Then a single bolt snaps, and the whole end of the bridge drops into the river.",
    "Luckily, the river was only two feet deep. Unluckily, the river was only two feet deep.",
    "You see, every bridge has a rhythm it naturally likes to sway at.",
    "Ever pushed a kid on a swing? Each push is tiny, but if they all land at just the right moment, the swing goes higher and higher.",
    "Seventy-four men stepping together were pushing that bridge like a swing.",
    "Nobody died, but the army made a rule: never cross a bridge in step.",
    "So now, the best drilled soldiers in the world cross every bridge like a crowd of tourists."
]

FULL_TEXT = " ".join(SCRIPT_LINES)
SR = 48000
DUR = 67.5

def build_word_timings(text, total_dur=65.5):
    words = text.split()
    per_w = total_dur / max(1, len(words))
    out = []
    t = 0.25
    for w in words:
        s = round(t, 3)
        e = round(t + per_w * 0.88, 3)
        out.append({"w": w, "s": s, "e": e})
        t += per_w
    return out

def main():
    words_list = build_word_timings(FULL_TEXT)
    with open(WORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(words_list, f, indent=2)
    print(f"[OK] Wrote {len(words_list)} word timings -> {WORDS_PATH}")

    mp3_tmp = os.path.join(HERE, "tmp_tts.mp3")
    tts_ok = False
    try:
        cmd = ["edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+12%", "--text", FULL_TEXT, "--write-media", mp3_tmp]
        if subprocess.run(cmd, capture_output=True).returncode == 0 and os.path.exists(mp3_tmp):
            ff = ["ffmpeg", "-y", "-i", mp3_tmp, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", WAV_PATH]
            if subprocess.run(ff, capture_output=True).returncode == 0:
                tts_ok = True
                print(f"[OK] Generated neural voiceover via edge-tts -> {WAV_PATH}")
    except Exception:
        pass

    if not tts_ok:
        print("[INFO] edge-tts/ffmpeg tidak terdeteksi, membuat synthesized vocal track 48kHz untuk mix.py...")
        n_samples = int(DUR * SR)
        t = np.arange(n_samples) / SR
        audio = np.zeros(n_samples, dtype=np.float32)
        for item in words_list:
            i0, i1 = int(item["s"] * SR), min(n_samples, int(item["e"] * SR))
            if i1 > i0:
                seg_t = t[i0:i1] - item["s"]
                env = np.sin(np.pi * np.linspace(0, 1, i1 - i0)) ** 0.5
                carrier = 0.18 * np.sin(2 * np.pi * 125 * seg_t) + 0.09 * np.sin(2 * np.pi * 250 * seg_t)
                audio[i0:i1] = carrier * env
        pcm16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
        wavfile.write(WAV_PATH, SR, pcm16)
        print(f"[OK] Wrote fallback 48kHz voice.wav -> {WAV_PATH}")

if __name__ == "__main__":
    main()
