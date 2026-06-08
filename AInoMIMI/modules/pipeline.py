import os
import json
from datetime import datetime
from .archiver import Archiver
from .surgeon import Surgeon, MODE_STANDARD, MODE_HYBRID
from .utils import clear_vram

class Pipeline:
    def __init__(self, separation_mode=MODE_STANDARD,
                 iterative=False, iterative_passes=2, blend_alpha=0.5, lyrics_accuracy="Standard", is_instrumental=False):
        self.archiver = Archiver()
        self.lyrics_accuracy = lyrics_accuracy
        self.is_instrumental = is_instrumental
        
        # インストモードなら強制的にStandard (Demucsのみ)
        actual_mode = MODE_STANDARD if is_instrumental else separation_mode
        
        self.surgeon = Surgeon(
            mode=actual_mode,
            iterative=iterative,
            iterative_passes=iterative_passes,
            blend_alpha=blend_alpha,
        )

    def run_phase1(self, input_path, progress_callback=None):
        """
        Phase 1: 分離とファイル整理の実行
        """
        try:
            # 1. 入力ファイルの更新日時チェック
            input_mtime = os.path.getmtime(input_path)
            
            # セッションパスの計算（まだ作成はしない）
            session_dir = self.archiver.create_session_dir(input_path, overwrite=False) 
            manifest_path = os.path.join(session_dir, "ai_context.json")
            
            should_skip_phase1 = False
            
            # 既存のManifestがある場合、タイムスタンプを比較
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        old_manifest = json.load(f)
                    
                    old_mtime = old_manifest.get("session_info", {}).get("mtime", 0)
                    
                    if abs(input_mtime - old_mtime) < 1.0: # 1秒以内の誤差なら同じとみなす
                        # さらにステムフォルダの中身もチェック
                        stems_dir = os.path.join(session_dir, "stems")
                        if os.path.exists(stems_dir) and len(os.listdir(stems_dir)) > 0:
                            should_skip_phase1 = True
                        else:
                            if progress_callback: progress_callback("Stems folder is empty. Re-running Phase 1.")
                    else:
                        if progress_callback: progress_callback(f"File change detected. Re-running Phase 1.")
                except Exception as e:
                    print(f"Error checking manifest: {e}")
            
            if should_skip_phase1:
                if progress_callback:
                    progress_callback("Existing result found & file unchanged. Skipping separation (Phase 1).")
                
                # Manifestをロードしておく
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

            else:
                # === Phase 1 実行（上書き） ===
                session_dir = self.archiver.create_session_dir(input_path, overwrite=True)
                temp_out = os.path.join(session_dir, "temp_demucs")
                os.makedirs(temp_out, exist_ok=True)
    
                # 2. 分離実行
                if progress_callback:
                    progress_callback("Initializing Surgeon (Demucs)...")
                
                filename_no_ext = os.path.splitext(os.path.basename(input_path))[0]
                self.surgeon.separate(input_path, temp_out, progress_callback)
    
                # 3. 整理
                if progress_callback:
                    progress_callback("Organizing files...")
                
                stems_dir = self.archiver.organize_stems(session_dir, temp_out, filename_no_ext)
    
                # 4. AI用JSONの雛形作成
                manifest = {
                    "session_info": {
                        "input_file": input_path,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "mtime": input_mtime # 更新日時を保存
                    },
                    "stems": {
                        f: os.path.join("stems", f) for f in os.listdir(stems_dir) if f.endswith(".wav")
                    },
                    "analysis": {} # Phase 2で埋める
                }
    
                with open(os.path.join(session_dir, "ai_context.json"), "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=4, ensure_ascii=False)
                
                if progress_callback:
                    progress_callback(f"Phase 1 Complete! Output: {session_dir}")
            
            # === Phase 2: The Analysts (Transcription & Analysis) ===
            
            # === Phase 2: The Analysts (Transcription & Analysis) ===
            from .analyst import Analyst
            analyst = Analyst()
            
            # 既存の解析結果があればロード（差分実行のため）
            analysis_results = {}
            json_path = os.path.join(session_dir, "analysis_report.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        analysis_results = json.load(f)
                except:
                    pass

            if progress_callback: progress_callback("Starting Phase 2: Analysis...")
            
            # ステムフォルダ内のファイルを列挙
            stem_files = [f for f in os.listdir(stems_dir) if f.endswith(".wav")]
            total_stems = len(stem_files)
            
            run_count = 0
            
            for i, stem_file in enumerate(stem_files):
                stem_path = os.path.join(stems_dir, stem_file)
                stem_type = os.path.splitext(stem_file)[0]
                
                # 既に解析済みで、かつエラーがない（またはエラー再試行したい？）場合はスキップ判定
                # ここでは「エラーが含まれていない」ならスキップとする
                prev_result = analysis_results.get(stem_type, {})
                
                # 簡易判定: タグ付け(tags)や歌詞(lyrics)などが含まれており、かつ "error" キーがないなら成功とみなす
                is_done = False
                if prev_result:
                    # エラーチェック
                    has_error = False
                    # errorキーが直下にあるか、またはネストされているか
                    if "error" in prev_result:
                        has_error = True
                    else:
                        for key, val in prev_result.items():
                            if isinstance(val, dict) and "error" in val:
                                has_error = True
                                break
                    
                    if not has_error:
                        # 何かしらの結果が入っているか？
                        # vocalsならlyrics、それ以外ならtagsかmidiがあればOKとする
                        if stem_type == "vocals":
                            if "lyrics" in prev_result:
                                is_done = True
                        else:
                            if "tags" in prev_result or "midi_path" in prev_result:
                                is_done = True
                        
                        # 共通してaudio_featuresは必須とみなすなら
                        if "audio_features" not in prev_result:
                            is_done = False

                if is_done:
                    if progress_callback: progress_callback(f"Skipping {stem_file} (Already analyzed).")
                    continue
                
                run_count += 1
                # 解析実行
                # 歌詞の精度判定
                transcribe_model = "large-v2" if (stem_type == "vocals" and self.lyrics_accuracy == "High") else "medium"
                
                # インストモード判定
                skip_transcription = self.is_instrumental
                
                stem_result = analyst.process_stem(
                    stem_path, 
                    stem_type, 
                    session_dir, 
                    progress_callback,
                    whisper_model=transcribe_model,
                    skip_transcription=skip_transcription
                )
                
                # 結果を統合（上書き）
                analysis_results[stem_type] = stem_result
                
                # [NEW] Phase 3.5 Deep Dive: Vocal Style
                if stem_type == "vocals":
                    try:
                        # Pitchデータがあれば渡す
                        pitch_data = stem_result.get("melody")
                        if not isinstance(pitch_data, list): pitch_data = None
                        
                        if progress_callback: progress_callback(f"Analyzing vocal style for {stem_file}...")
                        vocal_style = analyst.analyze_vocal_style(stem_path, pitch_data)
                        stem_result["vocal_style"] = vocal_style
                    except Exception as e:
                        print(f"Warning: Vocal style analysis failed: {e}")

            # ループ終了後、全体構造の解析
            if "structure" not in analysis_results:
                if progress_callback: progress_callback("Analyzing song structure...")
                try:
                    # 元ファイルを入力として構造解析
                    structure = analyst.analyze_structure(input_path)
                    analysis_results["structure"] = structure
                except Exception as e:
                    print(f"Warning: Structure analysis failed: {e}")
                    analysis_results["structure"] = {"error": str(e)}

            # マスター音源(2mix)全体解析 (Roadmap #6)
            if "master_mix" not in analysis_results:
                if progress_callback: progress_callback("Analyzing master mix (full 2mix)...")
                try:
                    master_result = analyst.analyze_master_mix(input_path, progress_callback)
                    analysis_results["master_mix"] = master_result
                except Exception as e:
                    print(f"Warning: Master mix analysis failed: {e}")
                    analysis_results["master_mix"] = {"error": str(e)}
                finally:
                    from .utils import clear_vram as _cv
                    _cv()

            # 汎用音声プロファイリング (Roadmap #5)
            if progress_callback: progress_callback("Generating voice profile...")
            try:
                from .profiler import VoiceProfiler
                profiler = VoiceProfiler()
                analysis_results["voice_profile"] = profiler.profile(analysis_results)
            except Exception as e:
                print(f"Warning: Voice profiling failed: {e}")
                analysis_results["voice_profile"] = {"error": str(e)}

            # [NEW] 歌詞・構成・楽器の統合 (作詞家視点)
            if progress_callback: progress_callback("Synthesizing script and structure...")
            try:
                analysis_results["lyric_script"] = analyst.synthesize_structure(analysis_results)
            except Exception as e:
                print(f"Warning: Structure synthesis failed: {e}")

            # [NEW] AIプロンプト生成 (Reverse Engineering)
            if progress_callback: progress_callback("Generating AI Prompts...")
            try:
                analysis_results["ai_prompts"] = analyst.generate_ai_prompt(analysis_results)
            except Exception as e:
                print(f"Warning: AI prompt generation failed: {e}")

            if run_count == 0:
                if progress_callback: progress_callback("All stems are already analyzed.")

            # 結果をJSON保存
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_results, f, indent=4, ensure_ascii=False)
                
            manifest["analysis_report"] = "analysis_report.json"
            
            # 更新されたManifestを保存
            manifest_path = os.path.join(session_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=4, ensure_ascii=False)

            if progress_callback:
                progress_callback(f"Pipeline Complete! Output: {session_dir}")

            return session_dir

        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise e
        finally:
            clear_vram()

    def run_pipeline(self, input_path, progress_callback=None):
        return self.run_phase1(input_path, progress_callback)
