import os
# import torch
import gc
import subprocess
# import librosa
# import numpy as np
import json

# ============================================================
# AudioSet ラベル分類マップ
# analyze_audioset() が返す527クラスのラベルを、
# genres / instruments / effects の3バケットに振り分ける。
# ★ 新しいラベルを拾いたくなったら、ここにキーワードを足すだけ。
# ============================================================
AUDIOSET_LABEL_KEYWORDS = {
    "genres": [
        "music", "rock", "pop", "hip hop", "jazz", "blues", "soul",
        "reggae", "ska", "punk", "metal", "grunge", "funk",
        "techno", "electronica", "drum and bass", "dubstep", "trance",
        "house", "ambient", "new-age", "classical", "opera",
        "country", "folk", "bluegrass", "flamenco", "swing",
        "gospel", "disco", "r&b", "latin", "salsa", "bossa nova",
        "soundtrack", "theme", "jingle", "psychedelic",
        "progressive", "indie", "alternative", "grindcore",
        "happy music", "sad music", "tender music", "exciting music",
        "angry music", "scary music", "orchestra", "symphonic", "overture",
        "ballad", "art pop", "avant-garde", "baroque", "renaissance",
    ],
    "instruments": [
        "guitar", "bass", "drum", "piano", "keyboard", "organ",
        "synthesizer", "violin", "viola", "cello", "harp",
        "trumpet", "trombone", "french horn", "saxophone", "clarinet",
        "flute", "oboe", "harmonica", "accordion", "banjo",
        "ukulele", "mandolin", "sitar", "tabla", "steelpan",
        "marimba", "xylophone", "vibraphone", "timpani",
        "cymbal", "hi-hat", "snare", "kick", "tom",
        "tambourine", "cowbell", "shaker", "bongo", "conga",
        "djembe", "gong", "bell", "chime", "nyckelharpa",
        "electric piano", "rhodes", "clavinet",
        "bagpipes", "didgeridoo", "fiddle",
        "orchestra", "string", "brass", "woodwind", "percussion",
        "plucked string", "bowed string", "choir", "vocal ensemble",
    ],
    "effects": [
        "distortion", "reverb", "echo", "chorus effect",
        "feedback", "delay", "tremolo", "vibrato",
        "wahwah", "phaser", "flanger",
        "scratching", "sampling", "loop",
        "strum", "pizzicato", "hammer-on", "pull-off",
        "power chord", "arpeggio", "glissando", "trill",
        "beatbox", "vocal percussion",
        "white noise", "static", "hum", "buzz",
        "clipping", "overdrive", "fuzz",
        "whispering", "breathing",
    ],
}

def _classify_audioset_label(label: str) -> str:
    """
    AudioSetのラベルを genres / instruments / effects に分類する。
    どれにも該当しなければ 'other' を返す。
    """
    label_lower = label.lower()
    for category, keywords in AUDIOSET_LABEL_KEYWORDS.items():
        for kw in keywords:
            if kw in label_lower:
                return category
    return "other"


class Analyst:
    def __init__(self, device=None):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[Analyst] Initialized on {self.device}")

    def _clear_vram(self):
        """VRAMを強制解放する"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def process_stem(self, stem_path, stem_type, output_dir, progress_callback=None, whisper_model="medium", skip_transcription=False):
        """
        ステムの種類に応じて最適な解析を行う
        vocab: vocals, bass, drums, other, guitar, piano
        """
        results = {}
        stem_filename = os.path.basename(stem_path)
        
        # 1. 基本オーディオ特徴量 (Librosa/CPU)
        if progress_callback: progress_callback(f"Analyzing audio features for {stem_filename}...")
        try:
            results["audio_features"] = self.analyze_audio_features(stem_path)
        except Exception as e:
            print(f"Warning: Audio feature analysis failed: {e}")
            results["audio_features"] = {"error": str(e)}

        # 2. AudioSet 詳細解析 (527クラス: ジャンル・楽器・FX)
        # ※ 旧 analyze_semantics (粗粒度ジャンル) は AudioSet が完全にカバーするため廃止
        if progress_callback: progress_callback(f"Deep-scanning with AudioSet for {stem_filename}...")
        try:
            results["audioset"] = self.analyze_audioset(stem_path)
        except Exception as e:
            msg = f"Warning: AudioSet analysis failed: {e}"
            print(msg)
            if progress_callback: progress_callback(msg)
            results["audioset"] = {"error": str(e)}
        finally:
            self._clear_vram()

        # 3. 音響・ミックス詳細解析 (Timbre) - 全ステム対象
        if progress_callback: progress_callback(f"Analyzing timbre & EQ for {stem_filename}...")
        try:
            results["timbre"] = self.analyze_timbre(stem_path)
        except Exception as e:
             print(f"Warning: Timbre analysis failed: {e}")
             results["timbre"] = {"error": str(e)}

        # 4. パート別詳細解析
        if stem_type == "vocals":
            # 歌詞解析
            if skip_transcription:
                if progress_callback: progress_callback("Skipping lyrics transcription (Instrumental/Skip mode).")
                results["lyrics"] = {"full_text": "(Instrumental)", "segments": []}
            else:
                if progress_callback: progress_callback(f"Transcribing lyrics for {stem_filename}...")
                try:
                    results["lyrics"] = self.transcribe_lyrics(stem_path)
                except Exception as e:
                    msg = f"Warning: Transcription failed: {e}"
                    print(msg)
                    results["lyrics"] = {"error": str(e)}
            
            # メロディ解析 (Pitch)
            if progress_callback: progress_callback(f"Analyzing melody lines for {stem_filename}...")
            try:
                results["melody"] = self.analyze_pitch(stem_path)
            except Exception as e:
                print(f"Warning: Melody analysis failed: {e}")
                results["melody"] = {"error": str(e)}

        elif stem_type == "bass":
            # ベースライン解析 (Pitch)
            if progress_callback: progress_callback(f"Analyzing bass lines for {stem_filename}...")
            try:
                results["melody"] = self.analyze_pitch(stem_path)
            except Exception as e:
                print(f"Warning: Bass line analysis failed: {e}")
                results["melody"] = {"error": str(e)}
        
        elif stem_type in ["other", "guitar", "piano"]:
            # コード進行解析
            if progress_callback: progress_callback(f"Analyzing chord progression for {stem_filename}...")
            try:
                results["chords"] = self.analyze_chords(stem_path)
            except Exception as e:
                print(f"Warning: Chord analysis failed: {e}")
                results["chords"] = {"error": str(e)}


            # MIDI化
            if progress_callback: progress_callback(f"Converting to MIDI for {stem_filename}...")
            try:
                midi_path = self.extract_midi(stem_path, output_dir)
                results["midi_path"] = midi_path
            except Exception as e:
                 # MIDIは必須ではないのでログだけ
                 # print(f"Warning: MIDI extraction failed: {e}") 
                 results["midi_path"] = None
        
        return results

    def analyze_audio_features(self, audio_path):
        """Librosaを使用したリズム・音圧・調性・リズムパターン解析"""
        y, sr = librosa.load(audio_path, sr=None)
        
        # ビートトラッキング
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        # RMSエネルギー（音圧）
        rms_arr = librosa.feature.rms(y=y)
        rms = float(rms_arr.mean())
        
        # スペクトル重心（明るさ）
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        
        # --- キー/スケール推定 ---
        key_info = self._estimate_key(y, sr)
        
        # --- LUFS推定 (簡易: RMSベース) ---
        lufs = self._estimate_lufs(rms_arr)
        
        # --- リズムパターン分類 ---
        rhythm_pattern = self._classify_rhythm(onset_env, float(tempo), sr)
        
        return {
            "tempo": float(tempo),
            "rms": rms,
            "spectral_brightness": float(spectral_centroid),
            "duration": float(librosa.get_duration(y=y, sr=sr)),
            "key": key_info,
            "lufs": lufs,
            "rhythm_pattern": rhythm_pattern,
        }

    def _estimate_key(self, y, sr):
        """クロマ特徴量からキー/スケール（メジャー/マイナー）を推定"""
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)  # 12ピッチクラスの平均強度
        
        pitch_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # メジャー/マイナーテンプレート (Krumhansl-Kessler)
        major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        best_key = "C"
        best_mode = "Major"
        best_corr = -1
        
        for shift in range(12):
            rolled = np.roll(chroma_mean, -shift)
            corr_maj = float(np.corrcoef(rolled, major_template)[0, 1])
            corr_min = float(np.corrcoef(rolled, minor_template)[0, 1])
            
            if corr_maj > best_corr:
                best_corr = corr_maj
                best_key = pitch_names[shift]
                best_mode = "Major"
            if corr_min > best_corr:
                best_corr = corr_min
                best_key = pitch_names[shift]
                best_mode = "Minor"
        
        return {
            "key": best_key,
            "mode": best_mode,
            "confidence": round(best_corr, 3),
            "label": f"{best_key} {best_mode}",
        }

    def _estimate_lufs(self, rms_arr):
        """RMSベースの簡易LUFS推定 (ITU-R BS.1770の近似)"""
        rms_mean = float(rms_arr.mean())
        if rms_mean > 0:
            # dBFS変換 + LUFS近似オフセット
            lufs_approx = 20 * np.log10(rms_mean) - 0.691
        else:
            lufs_approx = -70.0
        return round(float(lufs_approx), 1)

    def _classify_rhythm(self, onset_env, tempo, sr):
        """onset_strengthの自己相関パターンからリズムタイプを分類"""
        # テンポグラムで拍の細分割パターンを分析
        hop_length = 512
        
        # 自己相関でビートの周期性を取得
        ac = librosa.autocorrelate(onset_env, max_size=len(onset_env) // 2)
        if len(ac) < 10:
            return {"type": "Unknown", "regularity": 0.0}
        
        ac = ac / (ac[0] + 1e-8)  # 正規化
        
        # 拍間隔に対応するlag
        beat_lag = int(60.0 / tempo * sr / hop_length) if tempo > 0 else 100
        half_beat = beat_lag // 2
        quarter_beat = beat_lag // 4
        
        # 各拍位置の自己相関強度
        r_beat = float(ac[min(beat_lag, len(ac)-1)]) if beat_lag < len(ac) else 0
        r_half = float(ac[min(half_beat, len(ac)-1)]) if half_beat < len(ac) and half_beat > 0 else 0
        r_quarter = float(ac[min(quarter_beat, len(ac)-1)]) if quarter_beat < len(ac) and quarter_beat > 0 else 0
        
        # パターン分類ロジック
        regularity = r_beat  # ビートの規則性 (0-1)
        
        pattern = "Free/Irregular"
        if regularity > 0.3:
            if r_half > 0.4:
                # 半拍も強い = 4つ打ち / ストレートビート
                if r_quarter > 0.3:
                    pattern = "Four-on-the-floor"  # 4つ打ち
                else:
                    pattern = "Straight Beat"  # ストレートな2拍系
            elif r_half > 0.2:
                pattern = "Backbeat"  # バックビート (2,4拍強調)
            else:
                # 半拍が弱い = シャッフル/スウィング or 変拍子
                pattern = "Shuffle/Swing"
        elif regularity > 0.15:
            pattern = "Loose Groove"  # 緩いグルーヴ
        
        return {
            "type": pattern,
            "regularity": round(regularity, 3),
            "half_beat_strength": round(r_half, 3),
        }

    # [DEPRECATED] analyze_semantics は AudioSet (527クラス) が完全にカバーするため廃止。
    # 将来復元が必要な場合のためコメントとして残す。
    # def analyze_semantics(self, audio_path): ...

    def analyze_audioset(self, audio_path, top_k=20, min_score=0.05):
        """
        AudioSet (527クラス) による詳細な音響分類。
        ジャンル・楽器・FXを同時に検出し、3バケットに分類して返す。

        Returns:
            dict: {
                "genres":      [{"label": ..., "score": ...}, ...],
                "instruments": [...],
                "effects":     [...],
                "raw":         [...],  # 分類前の全ラベル (デバッグ用)
            }
        """
        from transformers import pipeline
        import librosa

        model_id = "MIT/ast-finetuned-audioset-10-10-0.4593"
        device = 0 if torch.cuda.is_available() else -1

        classifier = pipeline("audio-classification", model=model_id, device=device)

        # メモリ節約: 中央30秒を切り出して推論
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        max_samples = sr * 30
        if len(y) > max_samples:
            mid = len(y) // 2
            half = max_samples // 2
            y = y[mid - half : mid + half]

        raw_results = classifier({"array": y, "sampling_rate": sr}, top_k=top_k)

        # ラベルをバケットに振り分け
        buckets = {"genres": [], "instruments": [], "effects": [], "raw": []}
        for r in raw_results:
            label, score = r["label"], round(float(r["score"]), 4)
            if score < min_score:
                continue
            entry = {"label": label, "score": score}
            buckets["raw"].append(entry)
            category = _classify_audioset_label(label)
            if category in buckets:
                buckets[category].append(entry)

        return buckets

    def transcribe_lyrics(self, audio_path, model_size="large-v2"):
        """Whisperを使用した歌詞解析"""
        try:
            import whisper
            import librosa
        except ImportError:
            raise ImportError("openai-whisper library not found. Skipping transcription.")
        
        # VRAM節約のためデフォルトは medium だが、精度向上のため large も選択可能に
        print(f"Loading Whisper model: {model_size}...")
        try:
            model = whisper.load_model(model_size, device=self.device)
        except Exception as e:
            print(f"Warning: Failed to load {model_size}, falling back to medium. Error: {e}")
            model = whisper.load_model("medium", device=self.device)
        
        # FFmpeg依存を回避するため、librosaでロードしてからnumpy配列を渡す
        # Whisperは16kHz, モノラルを期待している
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        
        result = model.transcribe(y, verbose=False) # numpy arrayを渡す
        
        # 必要な情報だけ抽出
        segments = []
        for s in result["segments"]:
            segments.append({
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "text": s["text"].strip()
            })
            
        return {
            "language": result.get("language", "unknown"),
            "full_text": result["text"].strip(),
            "segments": segments
        }

    def synthesize_structure(self, analysis_results):
        """
        歌詞、構成、楽器情報の全データを統合し、
        [Section] (Instruments) "Lyrics" 形式の「脚本」を生成する。
        """
        structure_data = analysis_results.get("structure", {})
        if not structure_data or "error" in structure_data:
            return "Structure analysis data missing."
        
        # segments (以前の structure リスト相当) を取得
        segments = structure_data.get("sections", [])
        if not segments:
            # フォールバック: 旧形式の場合
            if isinstance(structure_data, list):
                segments = structure_data
            else:
                return "No structural sections found."

        vocals_data = analysis_results.get("vocals", {})
        lyrics = vocals_data.get("lyrics", {}).get("segments", [])
        
        # 他のステムの楽器情報を集める
        instrument_tags = {}
        for stem_type, data in analysis_results.items():
            if stem_type in ["vocals", "structure", "master_mix", "voice_profile", "lyric_script", "ai_prompts"]: continue
            if not isinstance(data, dict): continue
            audioset = data.get("audioset", {})
            instrs = [item["label"] for item in audioset.get("instruments", [])[:3]]
            if instrs:
                instrument_tags[stem_type] = instrs

        script = []
        for section in segments:
            if not isinstance(section, dict): continue
            start, end = section.get("start", 0), section.get("end", 0)
            label = section.get("label", "Section")
            
            # この区間に鳴っているであろう楽器
            all_instrs = []
            for tags in instrument_tags.values():
                all_instrs.extend(tags)
            unique_instrs = list(set(all_instrs))[:5]
            instr_str = ", ".join(unique_instrs)
            
            script.append(f"\n[{label}] ({instr_str})")
            
            # この区間に該当する歌詞を抽出
            section_lyrics = [s["text"] for s in lyrics if s["start"] >= start and s["start"] < end]
            for line in section_lyrics:
                script.append(line)
        
        return "\n".join(script)

    def generate_ai_prompt(self, analysis_results):
        """
        解析データから音楽生成AI用の英語プロンプトをリバースエンジニアリングする。
        """
        profile = analysis_results.get("voice_profile", {})
        master_data = analysis_results.get("master_mix", {})
        master_features = master_data.get("audio_features", {})
        master_audioset = master_data.get("audioset", {})
        
        # 基本情報
        tempo = round(master_features.get("tempo", 120))
        key = master_features.get("key", {}).get("label", "Unknown Key")
        rhythm = master_features.get("rhythm_pattern", {}).get("type", "Standard beat")
        
        # 楽器とジャンル
        genres = [g["label"] for g in master_audioset.get("genres", [])[:3]]
        instrs = []
        for stem in ["bass", "drums", "other", "guitar", "piano"]:
            stem_instrs = analysis_results.get(stem, {}).get("audioset", {}).get("instruments", [])
            instrs.extend([i["label"] for i in stem_instrs[:2]])
        unique_instrs = list(set(instrs))[:8]
        
        # ボーカル特性
        vocal_sig = profile.get("vocal", {}).get("signature", "Emotional vocals")

        # プロンプト組み立て
        prompt = f"Genre: {', '.join(genres)}. Style: {vocal_sig}. Instrumentation: {', '.join(unique_instrs)}. Tempo: {tempo} BPM. Key: {key}. Rhythmic Feel: {rhythm}. Atmospheric, high quality, professional mastering."
        
        return {
            "suno_style": prompt,
            "tags": genres + unique_instrs + [vocal_sig.split("、")[0]],
            "explanation": "This prompt was reverse-engineered from the audio analysis to recreate the song's vibe."
        }

    def analyze_pitch(self, audio_path):
        """Librosaを使用したメロディ/ピッチ解析 (pyin)"""
        # 負荷軽減のため、少し短めのフレームで解析するか、srを下げる
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        
        # 基本周波数 (f0) の推定
        # fmin=Note 'C2', fmax=Note 'C7' 程度に制限
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
        
        # 時系列データに変換
        melody_data = []
        hop_length = 512 # default for pyin
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
        
        for i, (t, freq) in enumerate(zip(times, f0)):
            if voiced_flag[i] and not np.isnan(freq):
                # MIDIノート番号への変換
                midi_note = librosa.hz_to_midi(freq)
                note_name = librosa.midi_to_note(int(round(midi_note)))
                
                # データ量削減のため、前のフレームと同じノートならスキップするか、変化点だけ記録する手もあるが
                # ここでは一定間隔（例えば0.1秒ごと）に間引いて記録する
                # 簡易的に全ての有声音を記録する（JSONが大きくなるが「丸裸」にするため）
                
                # ただし、全フレーム保存は重すぎるので、変化があった時だけ保存する（Run Length Encoding的アプローチ）
                # または0.1秒(=100ms)刻みでサンプリング
                
                # ここではシンプルに「発音区間」としてまとめる処理を入れると良さそうだが、
                # 生データに近い形で残す
                melody_data.append({
                    "time": round(float(t), 3),
                    "freq": round(float(freq), 2),
                    "midi": round(float(midi_note), 2),
                    "note": note_name
                })
        
        # データ量が膨大になるのを防ぐため、少し間引く (例: 5個に1個)
        # あるいはJSON保存時に圧縮されることを期待
        return melody_data[::5] if len(melody_data) > 1000 else melody_data

    def analyze_melody(self, audio_path):
        """
        メロディライン(Pitch)の解析
        """
        import librosa
        try:
            y, sr = librosa.load(audio_path, sr=22050)
        except Exception as e:
            # エラーハンドリングを追加
            print(f"Error loading audio for melody analysis: {e}")
            return [] # 空のリストを返すか、適切なエラー処理を行う

        # 基本周波数 (f0) の推定
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
        
        # 時系列データに変換
        melody_data = []
        hop_length = 512 # default for pyin
        times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
        
        for i, (t, freq) in enumerate(zip(times, f0)):
            if voiced_flag[i] and not np.isnan(freq):
                midi_note = librosa.hz_to_midi(freq)
                note_name = librosa.midi_to_note(int(round(midi_note)))
                melody_data.append({
                    "time": round(float(t), 3),
                    "freq": round(float(freq), 2),
                    "midi": round(float(midi_note), 2),
                    "note": note_name
                })
        
        return melody_data[::5] if len(melody_data) > 1000 else melody_data

    def analyze_chords(self, audio_path):
        """クロマ特徴量を用いた簡易コード進行推定"""
        y, sr = librosa.load(audio_path, sr=22050)
        
        # クロマグラムの計算 (CQT)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        
        # 時間軸の取得
        times = librosa.times_like(chroma, sr=sr)
        
        # コードテンプレート（メジャー・マイナー）
        # 簡易的に: 12音 x (Major, Minor) = 24通り
        # テンプレートマッチングを行う
        
        # ...の実装は複雑になるため、ここでは「主要なピッチクラス」を抽出する
        # 各フレームで最も強い音トップ3を記録して「和音の構成音」とする
        
        chord_progression = []
        # 0.5秒ごとにサンプリング
        samples_per_sec = sr / 512 # hop_length default
        step = int(samples_per_sec * 0.5) 
        if step < 1: step = 1
        
        pitches = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        for i in range(0, chroma.shape[1], step):
            col = chroma[:, i]
            # 強度が一定以下の場合は無音/ノイズとみなす
            if col.max() < 0.1:
                continue
                
            # 上位3音を取得
            top_indices = np.argsort(col)[::-1][:3]
            current_notes = [pitches[idx] for idx in top_indices]
            
            chord_progression.append({
                "time": round(float(times[i]), 2),
                "notes": current_notes,
                "strength": [round(float(col[idx]), 2) for idx in top_indices]
            })
            
        return chord_progression

    def analyze_timbre(self, audio_path):
        
        # 周波数帯域の定義
        low_idx = np.where(freqs < 250)[0]
        mid_idx = np.where((freqs >= 250) & (freqs < 4000))[0]
        high_idx = np.where(freqs >= 4000)[0]
        
        energy_total = np.sum(S) + 1e-6
        energy_low = np.sum(S[low_idx, :])
        energy_mid = np.sum(S[mid_idx, :])
        energy_high = np.sum(S[high_idx, :])
        
        eq_balance = {
            "low": round(float(energy_low / energy_total), 3),
            "mid": round(float(energy_mid / energy_total), 3),
            "high": round(float(energy_high / energy_total), 3)
        }
        
        # キャラクタ推定
        char = "Balanced"
        if eq_balance["low"] > 0.5: char = "Bass Heavy"
        elif eq_balance["high"] > 0.4: char = "Bright/Airy"
        elif eq_balance["low"] > 0.4 and eq_balance["high"] > 0.3: char = "V-Shape (Don-Shari)"
        elif eq_balance["mid"] > 0.6: char = "Mid-Forward (Radio)"
        
        # 2. 空間・ライブ感 (Spectral Flatness & Dynamic Range)
        # スペクトル平坦度が高い＝ノイズっぽい＝ライブ環境音や拍手、広がりが含まれる可能性
        flatness = librosa.feature.spectral_flatness(y=y).mean()
        
        # ダイナミックレンジ (RMSの最大と平均の差)
        rms = librosa.feature.rms(y=y)
        dynamic_range = np.max(rms) - np.mean(rms)
        
        # --- [NEW] Sound Engineer's Ear ---
        # 帯域別の重みをエンジニア的な言葉に変換
        mixing_balance = f"Low:{eq_balance['low']*100:.0f}%, Mid:{eq_balance['mid']*100:.0f}%, High:{eq_balance['high']*100:.0f}%"
        spatial_feel = "Wide/Deep" if flatness > 0.05 else "Directional/Mono-ish"
        impact = "Compressed/Consistent" if dynamic_range < 0.1 else "Dynamic/Impactful"
        
        engineer_report = {
            "balance": mixing_balance,
            "spatial_feel": spatial_feel,
            "dynamics_impact": impact,
            "technical_notes": f"EQ Character: {char}, Dominant Frequency: {'Low' if energy_low > energy_mid else 'Mid/High'}"
        }
        
        return {
            "eq_balance": eq_balance,
            "eq_character": char,
            "spatial": {
                "spectral_flatness": round(float(flatness), 4),
                "dynamic_range": round(float(dynamic_range), 4),
                "shout_out": "Live Atmosphere?" if flatness > 0.05 and dynamic_range > 0.1 else "Studio Clean"
            },
            "engineer_view": engineer_report
        }

    def analyze_vocal_style(self, audio_path, pitch_data=None):
        """ピッチ変動とスペクトルから歌唱表現を分析"""
        y, sr = librosa.load(audio_path, sr=22050)
        
        # 1. ビブラート/しゃくり検出
        # pitch_dataがあればそれを使う、なければ解析
        if not pitch_data:
            pitch_data = self.analyze_pitch(audio_path)
            
        # ピッチの微細な変動成分を抽出したいが、pyinの結果(pitch_data)は既に離散化・平滑化されている
        # 簡易的に、連続するノート間のピッチ変動係数を見る
        # 本当は生f0が必要
        
        # ブレス成分 (高域ノイズ比率)
        flatness = librosa.feature.spectral_flatness(y=y, n_fft=2048, hop_length=512)
        # 2kHz以上 (bin > 2048/2 * 2000/11025 ? いやsr=22050なのでNyquist=11025)
        # 簡易的に全体のflatness平均を使う
        breathiness = float(flatness.mean())
        
        # ダイナミクスの安定性 (RMSの分散)
        rms = librosa.feature.rms(y=y)
        dynamics_var = float(np.var(rms))
        
        style = "Standard"
        if breathiness > 0.05: style = "Airy/Whisper"
        elif dynamics_var > 0.005: style = "Expressive/Emotional"
        elif dynamics_var < 0.001: style = "Flat/Robotic"
        
        return {
            "breathiness": round(breathiness, 4),
            "dynamics_volatility": round(dynamics_var, 4),
            "style": style
        }

    def analyze_structure(self, audio_path):
        """楽曲の構成（繰り返し区間）を推定"""
        try:
            # 処理を軽くするためサンプリングレートを下げる
            y, sr = librosa.load(audio_path, sr=11025, mono=True)
            
            # Recurrence Matrixを用いた高度な推定は環境依存エラーが多いため
            # 今回は堅実なRMS(音量)ベースのサビ推定を採用する
            
            # RMSが高い区間 ＝ サビ(High Energy)と仮定
            rms = librosa.feature.rms(y=y)[0]
            times = librosa.times_like(rms, sr=sr)
            
            # 平滑化
            rms_norm = (rms - rms.min()) / (rms.max() - rms.min())
            
            # 閾値以上の区間を列挙
            high_energy_indices = np.where(rms_norm > 0.6)[0]
            
            segments = []
            if len(high_energy_indices) > 0:
                # 連続区間をまとめる
                diffs = np.diff(high_energy_indices)
                breaks = np.where(diffs > 50)[0] # 50フレーム(約1秒)以上空いたら別セクション
                
                start_idx = 0
                for b in breaks:
                    end_idx = b
                    seg_start = times[high_energy_indices[start_idx]]
                    seg_end = times[high_energy_indices[end_idx]]
                    
                    if seg_end - seg_start > 5.0: # 5秒以上あるならセクションとして認める
                        segments.append({
                            "start": round(float(seg_start), 2),
                            "end": round(float(seg_end), 2),
                            "label": "High Energy (Chorus?)"
                        })
                    start_idx = b + 1
            
            # 残りの部分
            if start_idx < len(high_energy_indices):
                seg_start = times[high_energy_indices[start_idx]]
                seg_end = times[high_energy_indices[-1]]
                if seg_end - seg_start > 5.0:
                     segments.append({
                            "start": round(float(seg_start), 2),
                            "end": round(float(seg_end), 2),
                            "label": "High Energy (Chorus?)"
                    })
            
            # フォールバック: セグメントが見つからなかった場合
            if not segments:
                duration = librosa.get_duration(y=y, sr=sr)
                segments.append({
                    "start": 0.0,
                    "end": round(float(duration), 2),
                    "label": "Main Section (Flat Dynamics)"
                })
            
            # --- [NEW] Arranger's Eye ---
            # セクション数やダイナミクスから構成のドラマを判定
            section_count = len(segments)
            is_dynamic = any(s["label"] == "High Energy (Chorus?)" for s in segments)
            
            drama_score = min(section_count * 20, 100) if is_dynamic else min(section_count * 10, 50)
            arrangement_type = "Progressive/Varied" if section_count > 3 else "Minimalist/Loop-based"
            
            arranger_view = {
                "drama_level": drama_score,
                "arrangement_type": arrangement_type,
                "structural_notes": f"Total sections: {section_count}. Main contrasts found in energy levels."
            }

            return {
                "sections": segments,
                "arranger_view": arranger_view
            }

        except Exception as e:
            print(f"Structure analysis failed: {e}")
            # エラーメッセージを短くする
            return {"error": str(e)[:100]}

    def analyze_master_mix(self, audio_path, progress_callback=None):
        """
        マスター音源(2mix)全体に AudioSet + librosa を適用。
        Stem分離前の楽曲全体としてのジャンル感・グルーヴを回収する。
        """
        results = {}
        
        # 1. 基本特徴量
        if progress_callback: progress_callback("Analyzing master mix features...")
        try:
            results["audio_features"] = self.analyze_audio_features(audio_path)
        except Exception as e:
            print(f"Warning: Master mix feature analysis failed: {e}")
            results["audio_features"] = {"error": str(e)}
        
        # 2. AudioSet (楽曲全体のジャンル感)
        if progress_callback: progress_callback("Deep-scanning master mix with AudioSet...")
        try:
            results["audioset"] = self.analyze_audioset(audio_path)
        except Exception as e:
            print(f"Warning: Master mix AudioSet failed: {e}")
            results["audioset"] = {"error": str(e)}
        finally:
            self._clear_vram()
        
        return results

    def extract_midi(self, audio_path, output_dir):
        """Basic Pitchを使用したMIDI変換 (Subprocess実行)"""
        # basic-pitch <output_dir> <input_audio>
        # TensorFlowを使用するため、メインプロセスのVRAMを汚さないようsubprocessで呼ぶ
        
        # コマンドの存在確認
        from shutil import which
        if which("basic-pitch") is None:
             # raise ImportError("basic-pitch command not found. Skipping MIDI extraction.")
             return None # 静かに終了

        cmd = ["basic-pitch", output_dir, audio_path]
        
        # 実行 (stdoutは抑制気味に)
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        # 生成されるファイル名を推測
        # basic-pitchはファイル名_basic_pitch.mid を生成する
        basename = os.path.splitext(os.path.basename(audio_path))[0]
        expected_midi = os.path.join(output_dir, f"{basename}_basic_pitch.mid")
        
        if os.path.exists(expected_midi):
            return expected_midi
        else:
            raise FileNotFoundError("Basic Pitch executed using subprocess but output file not found.")

