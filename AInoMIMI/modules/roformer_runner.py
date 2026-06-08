"""
BS-Roformer を使用したボーカル分離ランナー。
メインプロセスから直接呼び出す（サブプロセス不要）。

必要パッケージ: pip install bs-roformer huggingface_hub
モデル: model_bs_roformer_ep_317_sdr_12.9755.ckpt (HuggingFace)
"""

import os
import sys
import torch
import numpy as np
import soundfile as sf
import librosa
from huggingface_hub import hf_hub_download

# Add ZFTurbo's repository to sys.path to import their model implementation
zfturbo_path = os.path.join(os.path.dirname(__file__), 'zfturbo')
if zfturbo_path not in sys.path:
    sys.path.insert(0, zfturbo_path)

try:
    # Try importing from ZFTurbo's implementation first
    from models.bs_roformer.bs_roformer import BSRoformer
except ImportError:
    print("Warning: Failed to import BSRoformer from modules/zfturbo. trying standard import.")
    try:
        from bs_roformer import BSRoformer
    except ImportError:
        BSRoformer = None



# from .pipeline import ModelRunner  # Removed to avoid circular import and because it doesn't exist

# 推論チャンクサイズ (秒) — 公式推奨 chunk_size=352800 @ 44100Hz ≒ 8秒
CHUNK_SIZE = 8
OVERLAP = 2

class RoformerRunner:
    """
    BS-Roformer (Band-Split Rotary Transformer) を使用した音源分離。
    Vocal / Instrumental の2ステム分離に特化。
    num_stems=1 のため、vocalsマスクのみ出力し、instrumental = mix - vocals で算出。
    """

    # Config matching yaml: model_bs_roformer_ep_317_sdr_12.9755.yaml
    # https://huggingface.co/viperx/model_bs_roformer_ep_317_sdr_12.9755/blob/main/config.yaml
    DEFAULT_CONFIG = {
        "dim": 512,
        "depth": 12,
        "stereo": True,
        "num_stems": 1,
        "time_transformer_depth": 1,
        "freq_transformer_depth": 1,
        "linear_transformer_depth": 0,
        "freqs_per_bands": (
            2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  # 2 * 24 = 48
            4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,  # 4 * 12 = 48
            12, 12, 12, 12, 12, 12, 12, 12,  # 12 * 8 = 96
            24, 24, 24, 24, 24, 24, 24, 24,  # 24 * 8 = 192
            48, 48, 48, 48, 48, 48, 48, 48,  # 48 * 8 = 384
            128, 129  # = 257
            # Total = 1025
        ),
        "stft_n_fft": 2048,
        "stft_hop_length": 441,
        "stft_win_length": 2048,
        "stft_normalized": False,
        "mask_estimator_depth": 2,
        "multi_stft_resolution_loss_weight": 1.0,
    }

    def __init__(self, model_type='bs_roformer', config_path=None):
        import torch
        import numpy as np
        import soundfile as sf
        # import torch # Moved to load_model
        # import numpy as np # Kept global
        # import soundfile as sf # Kept global
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') # Moved to load_model
        self.device = None # Initialize as None, set in load_model
        self.model_type = model_type
        self.model = None
        self.config = None
        self.sr = 44100  # BS-Roformer is trained on 44.1kHz

    def load_model(self, progress_callback=None):
        if self.model is not None:
            return

        import torch
        import librosa
        from ml_collections import ConfigDict # Added as per instruction
        import yaml # Added as per instruction

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') # Moved here

        if BSRoformer is None:
            raise ImportError("BS-Roformer library not found or failed to import.")

        if progress_callback:
            progress_callback("Loading BS-Roformer model...")
        
        # Checkpoint download (viperx model)
        repo_id = "Eddycrack864/Music-Source-Separation-Training"
        filename = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
        
        try:
            ckpt_path = hf_hub_download(repo_id=repo_id, filename=filename)
            if progress_callback:
                progress_callback(f"BS-Roformer checkpoint found in cache: {ckpt_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to download BS-Roformer checkpoint: {e}")

        # Model initialization
        try:
            # ZFTurbo実装の引数セットを試す
            self.model = BSRoformer(**self.DEFAULT_CONFIG)
        except TypeError as e:
            if progress_callback:
                progress_callback(f"ZFTurbo config failed, trying minimal config: {e}")
            # 最小構成でリトライ
            minimal_config = {k: v for k, v in self.DEFAULT_CONFIG.items() 
                            if k in ['dim', 'depth', 'time_transformer_depth', 'freq_transformer_depth', 'freqs_per_bands']}
            minimal_config['num_stems'] = 1
            self.model = BSRoformer(**minimal_config)

        # Load checkpoint
        try:
            state_dict = torch.load(ckpt_path, map_location=self.device)
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            
            # 'model.' プレフィックスの除去
            new_state_dict = {}
            for k, v in state_dict.items():
                if k.startswith('model.'):
                    new_state_dict[k[6:]] = v
                else:
                    new_state_dict[k] = v
            
            self.model.load_state_dict(new_state_dict)
        except Exception as e:
            raise RuntimeError(f"Failed to load BS-Roformer weights: {e}")

        self.model.to(self.device)
        self.model.eval()
        if progress_callback:
            progress_callback(f"BS-Roformer loaded successfully on {self.device}.")

    def separate(self, audio_path, output_dir=None, progress_callback=None):
        """
        音声ファイルを Vocal と Instrumental に分離する。
        num_stems=1 なので、モデルはvocalsマスクのみ出力。
        instrumental = original_mix - vocals で算出。

        Returns:
            dict: {"vocals": path, "instrumental": path}
        """
        if self.model is None:
            self.load_model()

        import soundfile as sf
        import torch
        import numpy as np

        if progress_callback:
            progress_callback("BS-Roformer: Loading audio...")

        # Load audio
        mix, sr = librosa.load(audio_path, sr=self.sr, mono=False)
        if mix.ndim == 1:
            mix = np.stack([mix, mix])
        
        # Prepare input tensor
        mix_tensor = torch.from_numpy(mix).to(self.device).float()
        if mix_tensor.ndim == 2:
            mix_tensor = mix_tensor.unsqueeze(0)  # (1, channels, samples)

        if progress_callback:
            progress_callback("BS-Roformer: Separating vocals...")

        vocals_tensor = self._chunked_inference(mix_tensor, sr, progress_callback)

        # instrumental = mix - vocals (num_stems=1なのでマスク差分)
        # vocals_tensor: (channels, samples)
        # mix_tensor: (1, channels, samples)
        inst_tensor = mix_tensor.squeeze(0) - vocals_tensor

        # 保存
        os.makedirs(output_dir, exist_ok=True)
        vocals_path = os.path.join(output_dir, "vocals.wav")
        instrumental_path = os.path.join(output_dir, "instrumental.wav")

        vocals_np = vocals_tensor.cpu().numpy().T  # (samples, channels)
        inst_np = inst_tensor.cpu().numpy().T

        sf.write(vocals_path, vocals_np, sr)
        sf.write(instrumental_path, inst_np, sr)

        if progress_callback:
            progress_callback("BS-Roformer: Separation complete.")

        return {"vocals": vocals_path, "instrumental": instrumental_path}

    @torch.no_grad()
    def _chunked_inference(self, tensor, sr, progress_callback=None):
        """
        長い音声をチャンクに分割して推論し、オーバーラップで結合する。
        """
        chunk_samples = CHUNK_SIZE * sr
        overlap_samples = OVERLAP * sr
        step = chunk_samples - overlap_samples
        total_samples = tensor.shape[-1]
        
        # 出力バッファ: (channels, total_samples)
        channels = tensor.shape[1]
        output = torch.zeros(channels, total_samples, device=self.device)
        weight = torch.zeros(total_samples, device=self.device)
        
        # ウィンドウ（クロスフェード用）
        fade_len = overlap_samples
        if fade_len > 0:
            window = torch.ones(chunk_samples, device=self.device)
            fade_in = torch.linspace(0, 1, fade_len, device=self.device)
            fade_out = torch.linspace(1, 0, fade_len, device=self.device)
            window[:fade_len] = fade_in
            window[-fade_len:] = fade_out
        else:
             window = torch.ones(chunk_samples, device=self.device)
             
        num_chunks = max(1, (total_samples - overlap_samples + step - 1) // step)
        
        for i in range(0, total_samples, step):
            end = min(i + chunk_samples, total_samples)
            chunk = tensor[:, :, i:end]
            
            # パディング（最後のチャンクが短い場合）
            original_len = chunk.shape[-1]
            if original_len < chunk_samples:
                pad_size = chunk_samples - original_len
                chunk = torch.nn.functional.pad(chunk, (0, pad_size))
            
            # model output: (batch, num_stems=1, channels, samples)
            result = self.model(chunk)
            
            # (batch, num_stems, channels, samples) -> (channels, samples)
            result = result.squeeze(0)  # batch
            if result.ndim == 3 and result.shape[0] == 1:
                result = result.squeeze(0) # num_stems
            
            # クロップ
            chunk_res = result[:, :original_len]
            actual_len = end - i
            w = window[:actual_len]
            
            output[:, i:end] += chunk_res * w.unsqueeze(0)
            weight[i:end] += w
            
            chunk_idx = i // step + 1
            if progress_callback and chunk_idx % 2 == 0:
                 # 頻繁すぎる更新を避ける
                pass
                
        # 正規化
        weight = weight.clamp(min=1e-8)
        output = output / weight.unsqueeze(0)
        
        return output

    def cleanup(self):
        """モデルをアンロードしてVRAMを解放"""
        if self.model is not None:
            del self.model
            self.model = None
        torch.cuda.empty_cache()
        import gc
        gc.collect()
