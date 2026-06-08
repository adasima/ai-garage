import os
import shutil
from datetime import datetime

class Archiver:
    def __init__(self, base_output_dir="output"):
        self.base_output_dir = base_output_dir
        if not os.path.exists(self.base_output_dir):
            os.makedirs(self.base_output_dir)

    def create_session_dir(self, input_path, overwrite=True):
        """
        曲名からセッション用フォルダを作成する
        overwrite=True の場合、既存フォルダを削除して作り直す
        overwrite=False の場合、既存フォルダがあればそのままそのパスを返す
        """
        filename = os.path.splitext(os.path.basename(input_path))[0]
        # ファイル名に使えない文字を置換するなど簡易的なサニタイズ推奨だが、一旦そのまま
        session_name = filename
        session_dir = os.path.join(self.base_output_dir, session_name)
        
        # 冗長にしない：既存フォルダがある場合は容赦なく削除して作り直す (overwrite=True時)
        if overwrite and os.path.exists(session_dir):
            import time
            max_retries = 3
            for i in range(max_retries):
                try:
                    shutil.rmtree(session_dir)
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        print(f"Cleanup retry {i+1}/{max_retries} due to: {e}")
                        time.sleep(1)
                    else:
                         print(f"Warning: Failed to clean up existing directory {session_dir}: {e}")
        
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    def organize_stems(self, session_dir, demucs_out_dir, filename_no_ext):
        """
        Demucsの深い階層から session_dir/stems/ 直下にファイルを移動する
        """
        stems_dir = os.path.join(session_dir, "stems")
        os.makedirs(stems_dir, exist_ok=True)
        
        # Demucsのデフォルト出力先: {demucs_out_dir}/htdemucs_6s/{track_name}/*.wav
        # track_nameは、Surgeonでリネーム(temp_input)された可能性があるため、決め打ちできない。
        # htdemucs_6s直下にあるフォルダを探索する。
        base_search_dir = os.path.join(demucs_out_dir, "htdemucs_6s")
        
        if os.path.exists(base_search_dir):
            # フォルダを列挙
            subdirs = [d for d in os.listdir(base_search_dir) if os.path.isdir(os.path.join(base_search_dir, d))]
            
            for d in subdirs:
                src_dir = os.path.join(base_search_dir, d)
                
                # wavファイルを移動
                for f in os.listdir(src_dir):
                    if f.endswith(".wav"):
                         shutil.move(os.path.join(src_dir, f), os.path.join(stems_dir, f))
            
            # 元の空フォルダを削除 (WinError 5対策のリトライ)
            import time
            max_retries = 3
            for i in range(max_retries):
                try:
                    shutil.rmtree(demucs_out_dir)
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        print(f"Cleanup retry {i+1}/{max_retries} due to: {e}")
                        time.sleep(1)
                    else:
                         print(f"Warning: Failed to clean up temp directory {demucs_out_dir}: {e}")
            
        return stems_dir
