#!/usr/bin/env bash
set -e
echo "=========================================================="
echo " Stickman Paperbag - GitHub Codespaces & Cloud Runner"
echo " (Remotion + Three.js + Python Audio DSP + FFmpeg)"
echo "=========================================================="

mkdir -p out public/bridge/kenney

# Copy GitHub Actions workflow to repo root if running inside a git repository
if [ -d "../.git" ] && [ -f ".github/workflows/render-mp4.yml" ]; then
  mkdir -p ../.github/workflows
  cp .github/workflows/render-mp4.yml ../.github/workflows/render-mp4.yml
  echo "[OK] Installed GitHub Actions workflow -> ../.github/workflows/render-mp4.yml"
fi

echo "[1/4] Menginstal dependencies Python & Node..."
pip install numpy scipy edge-tts --quiet || true
npm install

echo "[2/4] Membuat Voiceover 48kHz (voice.wav) & Word Timings (words.json)..."
python3 templates/voice/generate_voice.py

echo "[3/4] Merender Audio Mix (SFX + March Score + Auto-Ducking) -> templates/audio/mix.wav..."
python3 templates/audio/mix.py

FRAMES_ARG=""
if [ -n "$1" ]; then
  FRAMES_ARG="--frames=$1"
  echo "[4/4] Merender 3D Video (Frame $1) & Menggabungkan Audio (FFmpeg)..."
else
  echo "[4/4] Merender Full 3D Video (2025 Frames) & Menggabungkan Audio (FFmpeg)..."
fi

npx remotion render src/index.ts BridgeShort out/video_silent.mp4 $FRAMES_ARG --codec h264 --crf 18 --gl=angle
ffmpeg -y -i out/video_silent.mp4 -i templates/audio/mix.wav -c:v copy -c:a aac -b:a 192k -map 0:v:0 -map 1:a:0 -shortest out/final_paperbag_short.mp4

echo "=========================================================="
echo " SELESAI! File MP4 siap di: out/final_paperbag_short.mp4"
echo "=========================================================="
