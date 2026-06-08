import torch
import gc

def clear_vram():
    """VRAMとシステムメモリを強制的に解放するヘルパー関数"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()
