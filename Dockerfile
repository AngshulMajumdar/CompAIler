FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang-14 lld-14 wasi-libc libclang-rt-14-dev-wasm32 build-essential cmake ninja-build ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/compailer
COPY . .
RUN pip install . && CMAKE_ARGS='-DGGML_CUDA=OFF -DGGML_NATIVE=OFF' pip install llama-cpp-python==0.3.36 --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
    && useradd -m -u 1000 user
USER user
ENV HOME=/home/user COMPAILER_THREADS=2 COMPAILER_WORKERS=2
WORKDIR /work
ENTRYPOINT ["compailer"]
