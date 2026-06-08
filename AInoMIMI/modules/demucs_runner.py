import os
import sys
import numpy as np

# ================================================
# torchaudio の torchcodec 依存を完全に回避する
# 方針: torchaudio.load / torchaudio.save を
#        soundfile ベースの関数で差し替える（モンキーパッチ）
# これにより torchaudio のバックエンド設定に依存しなくなる
# ================================================

import torch
import soundfile as sf
import torchaudio

def _patched_load(filepath, *args, **kwargs):
    """soundfile を使って音声を読み込む。torchaudio.load の代替。"""
    filepath = str(filepath)
    data, samplerate = sf.read(filepath, dtype='float32')
    # soundfile: (samples, channels) → torch: (channels, samples)
    if data.ndim == 1:
        tensor = torch.from_numpy(data).unsqueeze(0)
    else:
        tensor = torch.from_numpy(data.T)
    return tensor, samplerate

def _patched_save(filepath, src, sample_rate, *args, **kwargs):
    """soundfile を使って音声を書き出す。torchaudio.save の代替。"""
    filepath = str(filepath)
    # torch: (channels, samples) → soundfile: (samples, channels)
    if src.dim() == 1:
        data = src.numpy()
    else:
        data = src.T.numpy()
    sf.write(filepath, data, sample_rate)

# パッチ適用
torchaudio.load = _patched_load
torchaudio.save = _patched_save
print("[Runner] torchaudio.load/save patched to use soundfile (torchcodec bypassed)")

# ここでやっと Demucs をインポート＆実行
try:
    from demucs.separate import main
    
    print("[Runner] Starting Demucs...")
    main(sys.argv[1:])

except Exception as e:
    print(f"[Runner] Execution Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
