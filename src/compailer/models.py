"""Checksum-verified, public CPU GGUF model download."""
import hashlib
import os
from pathlib import Path
import urllib.request

REPO='Qwen/Qwen2.5-Coder-7B-Instruct-GGUF'
REVISION='f0d2d3bb1a8cbc83ff1f890f98ac35ac5f219b2c'
NAME='qwen2.5-coder-7b-instruct-q4_k_m.gguf'
SHA256='509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c'
SIZE=4683073536

def default_path():
    return Path(os.environ.get('COMPAILER_MODEL_DIR',str(Path.home()/'.cache/compailer')))/NAME

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''): h.update(b)
    return h.hexdigest()

def download():
    target=default_path(); target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.stat().st_size==SIZE and digest(target)==SHA256: return target
        raise ValueError('Existing model checksum mismatch; remove the damaged file first')
    part=target.with_suffix('.partial'); h=hashlib.sha256(); count=0
    try:
        print('Downloading CPU model (4.68 GB); no API key required.',flush=True)
        with urllib.request.urlopen(f'https://huggingface.co/{REPO}/resolve/{REVISION}/{NAME}',timeout=120) as r,part.open('wb') as f:
            while block:=r.read(4*1024**2):
                f.write(block); h.update(block); count+=len(block)
        if count!=SIZE or h.hexdigest()!=SHA256: raise ValueError('Downloaded model failed checksum validation')
        part.replace(target)
    except BaseException:
        part.unlink(missing_ok=True); raise
    return target
