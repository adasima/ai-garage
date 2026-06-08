import os
import subprocess
# import torch
# import numpy as np
# import soundfile as sf
from .utils import clear_vram


# --- 分離モード定数 ---
MODE_STANDARD = "standard"         # Demucs 6s のみ (従来)
MODE_HYBRID   = "hybrid"           # BS-Roformer(Vocal) + Demucs(Inst)


class Surgeon:
    def __init__(self, model_name="htdemucs_6s", mode=MODE_STANDARD,
                 iterative=False, iterative_passes=2, blend_alpha=0.5):
        """
        Args:
            model_name: Demucs モデル名
            mode: 分離モード ("standard" or "hybrid")
            iterative: 反復ブレンド分離を有効にするか
            iterative_passes: 反復回数 (2-3推奨)
            blend_alpha: ブレンド比率 (0-1, 高いほど原曲寄り)
        """
        self.model_name = model_name
        self.mode = mode
        self.iterative = iterative
        self.iterative_passes = max(1, min(iterative_passes, 5))
        self.blend_alpha = blend_alpha

    def separate(self, input_path, output_root, progress_callback=None):
        """
        音源分離のメインエントリポイント。
        modeに応じて Standard / Hybrid を切り替える。
        """
        if progress_callback:
            progress_callback(f"Separation started (mode={self.mode})...")

        os.environ["TORCHAUDIO_BACKEND"] = "soundfile"

        if self.mode == MODE_HYBRID:
            result = self._hybrid_separate(input_path, output_root, progress_callback)
        else:
            result = self._standard_separate(input_path, output_root, progress_callback)

        # 無音ファイルの削除
        self._remove_silent_files(output_root, progress_callback)

        if progress_callback:
            progress_callback("Separation finished. VRAM cleared.")

        return result

    # =========================================================
    # Standard: Demucs 6s のみ（従来のロジック）
    # =========================================================
    def _standard_separate(self, input_path, output_root, progress_callback=None):
        """従来の Demucs サブプロセス分離"""
        import sys

        temp_wav = None
        target_input = input_path

        try:
            if not input_path.lower().endswith(".wav"):
                if progress_callback:
                    progress_callback(f"Pre-converting {os.path.basename(input_path)} to temporary WAV...")
                temp_wav = os.path.join(output_root, "temp_input.wav")
                os.makedirs(output_root, exist_ok=True)
                import soundfile as sf
                data, samplerate = sf.read(input_path)
                sf.write(temp_wav, data, samplerate)
                target_input = temp_wav
                if progress_callback:
                    progress_callback("Pre-conversion complete.")

            runner_script = os.path.join(os.path.dirname(__file__), "demucs_runner.py")

            cmd = [
                sys.executable,
                runner_script,
                "-n", self.model_name,
                "-o", output_root,
                target_input
            ]

            # [FIX] UnicodeEncodeError対策: 環境変数でUTF-8を強制
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', env=env)

            output_log = []
            for line in process.stdout:
                line = line.strip()
                if line:
                    output_log.append(line)
                    if progress_callback:
                        if "%" in line or "Error" in line or "Traceback" in line:
                            progress_callback(f"Processing: {line}")

            process.wait()

            if process.returncode != 0:
                full_log = "\n".join(output_log[-10:])
                raise Exception(f"Demucs failed with code {process.returncode}.\nLog:\n{full_log}")

        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass
            clear_vram()

        return True

    # =========================================================
    # Hybrid: BS-Roformer (Vocal) + Demucs (Instruments)
    # =========================================================
    def _hybrid_separate(self, input_path, output_root, progress_callback=None):
        """
        2パスハイブリッド分離:
        1. BS-Roformer で Vocal / Instrumental に分離
        2. Instrumental を Demucs に入力して楽器パートに分離
        3. Roformerの Vocal + Demucsの楽器パートを最終出力にする
        """
        from .roformer_runner import RoformerRunner

        os.makedirs(output_root, exist_ok=True)

        # WAV事前変換
        temp_wav = None
        if not input_path.lower().endswith(".wav"):
            if progress_callback:
                progress_callback(f"Pre-converting to WAV...")
            temp_wav = os.path.join(output_root, "temp_input.wav")
            import soundfile as sf
            data, samplerate = sf.read(input_path)
            sf.write(temp_wav, data, samplerate)
            wav_path = temp_wav
        else:
            wav_path = input_path

        try:
            # === Pass 1: BS-Roformer (Vocal / Instrumental) ===
            if progress_callback:
                progress_callback("Pass 1: BS-Roformer (Vocal extraction)...")

            roformer = RoformerRunner()
            roformer_out = os.path.join(output_root, "roformer_temp")
            os.makedirs(roformer_out, exist_ok=True)

            # 反復ブレンドが有効な場合はそちらを使う
            if self.iterative and self.iterative_passes > 1:
                rf_result = self._iterative_roformer(
                    roformer, wav_path, roformer_out, progress_callback
                )
            else:
                rf_result = roformer.separate(wav_path, roformer_out, progress_callback)

            vocals_path = rf_result["vocals"]
            inst_path = rf_result["instrumental"]

            # Roformer のモデルを解放 (VRAM節約)
            roformer.cleanup()
            clear_vram()
            if progress_callback:
                progress_callback("Pass 1 complete. Roformer unloaded, VRAM cleared.")

            # === Pass 2: Demucs (Instrumental → 楽器パート) ===
            if progress_callback:
                progress_callback("Pass 2: Demucs (Instrument separation)...")

            demucs_out = os.path.join(output_root, "demucs_temp")
            os.makedirs(demucs_out, exist_ok=True)

            self._run_demucs_on_file(inst_path, demucs_out, progress_callback)

            # === 結果の統合 ===
            if progress_callback:
                progress_callback("Merging hybrid results...")

            self._merge_hybrid_results(
                output_root, vocals_path, demucs_out, progress_callback
            )

        finally:
            # 一時ファイルの掃除
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except:
                    pass

            # 一時ディレクトリの掃除
            import shutil
            for d in ["roformer_temp", "demucs_temp"]:
                p = os.path.join(output_root, d)
                if os.path.exists(p):
                    try:
                        shutil.rmtree(p)
                    except:
                        pass

            clear_vram()

        return True

    def _run_demucs_on_file(self, audio_path, output_dir, progress_callback=None):
        """指定ファイルに対して Demucs を実行する"""
        import sys

        runner_script = os.path.join(os.path.dirname(__file__), "demucs_runner.py")

        cmd = [
            sys.executable,
            runner_script,
            "-n", self.model_name,
            "-o", output_dir,
            audio_path
        ]

        # [FIX] UnicodeEncodeError対策
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', env=env)

        output_log = []
        for line in process.stdout:
            line = line.strip()
            if line:
                output_log.append(line)
                if progress_callback:
                    if "%" in line or "Error" in line or "Traceback" in line:
                        progress_callback(f"Demucs: {line}")

        process.wait()

        if process.returncode != 0:
            full_log = "\n".join(output_log[-10:])
            raise Exception(f"Demucs failed with code {process.returncode}.\nLog:\n{full_log}")

    def _merge_hybrid_results(self, output_root, vocals_path, demucs_out, progress_callback=None):
        """
        Roformerのvocals + Demucsの楽器パートを最終出力ディレクトリに統合。
        Demucsのvocalsは廃棄し、Roformer版を採用。
        """
        import glob
        import shutil

        # Demucsの出力を探す (output_dir/model_name/filename/*.wav)
        demucs_wavs = glob.glob(os.path.join(demucs_out, "**", "*.wav"), recursive=True)

        # 最終出力用のフォルダ（Demucsの標準出力構造を模倣）
        # pipeline.py の organize_stems が期待する構造:
        # output_root / model_name / filename_noext / *.wav
        # → Demucsの出力をそのまま移動し、vocalsだけRoformer版に差し替え

        for wav in demucs_wavs:
            basename = os.path.basename(wav).lower()

            if basename.startswith("vocal"):
                # Demucsのvocalsは廃棄（Roformer版を使う）
                continue

            # 楽器パートをoutput_rootのDemucs構造にコピー
            # パスの相対構造を維持
            rel = os.path.relpath(wav, demucs_out)
            dest = os.path.join(output_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(wav, dest)

        # Roformerのvocalsを同じ場所に配置
        if demucs_wavs:
            # Demucsの出力先ディレクトリを推定
            sample_rel = os.path.relpath(demucs_wavs[0], demucs_out)
            stem_dir = os.path.join(output_root, os.path.dirname(sample_rel))
            os.makedirs(stem_dir, exist_ok=True)
            dest_vocals = os.path.join(stem_dir, "vocals.wav")
            shutil.copy2(vocals_path, dest_vocals)

            if progress_callback:
                progress_callback(f"Hybrid merge: Roformer vocals + Demucs instruments → {stem_dir}")
        else:
            # Demucsの出力がない場合のフォールバック
            dest = os.path.join(output_root, self.model_name, "hybrid_output")
            os.makedirs(dest, exist_ok=True)
            shutil.copy2(vocals_path, os.path.join(dest, "vocals.wav"))
            if progress_callback:
                progress_callback("Warning: No Demucs output found. Vocals-only output created.")

    # =========================================================
    # Iterative Blending (反復ブレンド分離)
    # =========================================================
    def _iterative_roformer(self, roformer, audio_path, output_dir, progress_callback=None):
        """
        反復ブレンド分離: Zang et al. (2025) の手法。
        Input[t+1] = α * Original + (1-α) * Reconstructed[t]
        """
        if progress_callback:
            progress_callback(
                f"Iterative blending enabled: {self.iterative_passes} passes, α={self.blend_alpha}"
            )

        # 原曲を読み込み
        import soundfile as sf
        import numpy as np
        original, sr = sf.read(audio_path, dtype="float32")
        if original.ndim == 1:
            original = np.stack([original, original], axis=-1)

        current_input_path = audio_path
        result = None

        for step in range(self.iterative_passes):
            if progress_callback:
                progress_callback(f"Iterative pass {step + 1}/{self.iterative_passes}...")

            # 分離実行
            step_dir = os.path.join(output_dir, f"iter_step_{step}")
            os.makedirs(step_dir, exist_ok=True)
            result = roformer.separate(current_input_path, step_dir, progress_callback)

            # 最終パスならここで終了
            if step == self.iterative_passes - 1:
                break

            # 再構成: vocals + instrumental を加算
            vocals_data, _ = sf.read(result["vocals"], dtype="float32")
            inst_data, _ = sf.read(result["instrumental"], dtype="float32")

            if vocals_data.ndim == 1:
                vocals_data = np.stack([vocals_data, vocals_data], axis=-1)
            if inst_data.ndim == 1:
                inst_data = np.stack([inst_data, inst_data], axis=-1)

            reconstructed = vocals_data + inst_data

            # ブレンド: α * original + (1-α) * reconstructed
            # 長さを揃える
            min_len = min(len(original), len(reconstructed))
            blended = (
                self.blend_alpha * original[:min_len]
                + (1 - self.blend_alpha) * reconstructed[:min_len]
            )

            # ブレンド結果を次のパスの入力として保存
            blended_path = os.path.join(output_dir, f"blended_step_{step}.wav")
            sf.write(blended_path, blended, sr)
            current_input_path = blended_path

            if progress_callback:
                progress_callback(f"Iterative pass {step + 1} complete. Blended for next pass.")

        # 最終結果を output_dir 直下にコピー
        import shutil
        final_vocals = os.path.join(output_dir, "vocals.wav")
        final_inst = os.path.join(output_dir, "instrumental.wav")

        if result:
            shutil.copy2(result["vocals"], final_vocals)
            shutil.copy2(result["instrumental"], final_inst)

        # 中間ファイルの掃除
        for step in range(self.iterative_passes):
            step_dir = os.path.join(output_dir, f"iter_step_{step}")
            if os.path.exists(step_dir):
                try:
                    shutil.rmtree(step_dir)
                except:
                    pass
            blended_path = os.path.join(output_dir, f"blended_step_{step}.wav")
            if os.path.exists(blended_path):
                try:
                    os.remove(blended_path)
                except:
                    pass

        return {"vocals": final_vocals, "instrumental": final_inst}

    # =========================================================
    # ユーティリティ
    # =========================================================
    def _remove_silent_files(self, output_root, progress_callback=None, threshold_db=-75.0):
        """
        生成されたステムの中に、実質的に無音（閾値以下）のものがあれば削除する。
        """
        import glob

        wav_files = glob.glob(os.path.join(output_root, "**", "*.wav"), recursive=True)

        for wav_path in wav_files:
            try:
                import soundfile as sf
                import numpy as np
                data, samplerate = sf.read(wav_path)

                if len(data) == 0:
                    rms = 0
                else:
                    rms = np.sqrt(np.mean(data**2))

                if rms > 0:
                    db = 20 * np.log10(rms)
                else:
                    db = -float('inf')

                if db < threshold_db:
                    filename = os.path.basename(wav_path)
                    print(f"Removing silent track: {filename} ({db:.1f} dB)")
                    if progress_callback:
                        progress_callback(f"Removing silent track: {filename} (Volume: {db:.1f} dB)")
                    os.remove(wav_path)

            except Exception as e:
                print(f"Error checking silence for {wav_path}: {e}")
