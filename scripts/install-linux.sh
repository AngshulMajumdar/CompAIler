#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential cmake ninja-build clang-14 lld-14 wasi-libc libclang-rt-14-dev-wasm32 tcc bubblewrap libseccomp2
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .
CMAKE_ARGS='-DGGML_CUDA=OFF -DGGML_NATIVE=OFF' .venv/bin/python -m pip install llama-cpp-python==0.3.36 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
.venv/bin/compailer doctor
printf '\nInstalled. Activate with: source .venv/bin/activate\nDownload model with: compailer model download\n'
