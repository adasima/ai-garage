"""
VoiceProfiler: 汎用音声プロファイリングモジュール

解析済みデータ (analysis_report.json) を入力とし、
「人間が聞い たとき、ああこの音はこれっぽいな」と判断できるレベルの
定量データと自然言語テキスト (signature) を生成する。

設計方針:
- 各軸は INSTRUMENT_AXES / VOCAL_AXES 辞書で定義 → 追加・削除は辞書編集のみ
- 各 _score_xxx() メソッドは独立 → 個別に差し替え・調整可能
- レーダーチャート用データ構造を自動生成
"""
import numpy as np


# ============================================================
# 軸定義: 辞書ベースで管理。追加・削除はここだけ。
# "scorer" の文字列が _score_xxx メソッド名に対応する。
# ============================================================

INSTRUMENT_AXES = {
    "tempo_energy":  {"name": "テンポ感",       "scorer": "_score_tempo"},
    "sparkle":       {"name": "キラキラ・輝度",  "scorer": "_score_sparkle"},
    "beat_stability":{"name": "ビート安定度",    "scorer": "_score_beat_stability"},
    "pop_affinity":  {"name": "Pop適合度",       "scorer": "_score_pop_affinity"},
    "brightness":    {"name": "華やかさ",        "scorer": "_score_brightness"},
    "heaviness":     {"name": "重厚感",          "scorer": "_score_heaviness"},
    "electronic":    {"name": "電子感",          "scorer": "_score_electronic"},
    "organic":       {"name": "生演奏感",        "scorer": "_score_organic"},
}

VOCAL_AXES = {
    "voice_brightness":  {"name": "声の明るさ",       "scorer": "_score_voice_brightness"},
    "breathiness":       {"name": "息遣い・ウィスパー", "scorer": "_score_breathiness"},
    "pitch_stability":   {"name": "音程安定度",       "scorer": "_score_pitch_stability"},
    "register_height":   {"name": "声域の高さ",       "scorer": "_score_register_height"},
    "power":             {"name": "パワー・声量",      "scorer": "_score_power"},
    "lightness":         {"name": "軽やかさ",         "scorer": "_score_lightness"},
    "vibrato_intensity": {"name": "ビブラート強度",    "scorer": "_score_vibrato"},
    "vocal_range":       {"name": "音域幅",           "scorer": "_score_vocal_range"},
}


class VoiceProfiler:
    """
    解析済みデータを受け取り、多角的なプロファイルを生成する。
    """

    def profile(self, analysis_data: dict) -> dict:
        """
        メインエントリポイント。
        analysis_data: analysis_report.json の内容全体
        """
        instrument_scores = self._score_instrument(analysis_data)
        vocal_scores = self._score_vocal(analysis_data)

        # 各カテゴリの平均 (overall)
        inst_values = [v for v in instrument_scores.values() if isinstance(v, (int, float))]
        vocal_values = [v for v in vocal_scores.values() if isinstance(v, (int, float))]

        inst_overall = round(np.mean(inst_values), 1) if inst_values else 0
        vocal_overall = round(np.mean(vocal_values), 1) if vocal_values else 0
        total_score = round((inst_overall + vocal_overall) / 2, 1)

        # シグネチャ生成
        inst_sig = self._generate_instrument_signature(instrument_scores, analysis_data)
        vocal_sig = self._generate_vocal_signature(vocal_scores, analysis_data)
        combined_sig = self._generate_combined_signature(
            instrument_scores, vocal_scores, analysis_data, inst_sig, vocal_sig
        )

        # レーダーチャートデータ
        radar_labels = []
        radar_inst = []
        radar_vocal = []
        for key, axis_def in INSTRUMENT_AXES.items():
            radar_labels.append(axis_def["name"])
            radar_inst.append(instrument_scores.get(key, 0))
        for key, axis_def in VOCAL_AXES.items():
            radar_labels.append(axis_def["name"])
            radar_vocal.append(vocal_scores.get(key, 0))

        return {
            "instrument": {
                "axes": instrument_scores,
                "overall": inst_overall,
                "signature": inst_sig,
            },
            "vocal": {
                "axes": vocal_scores,
                "overall": vocal_overall,
                "signature": vocal_sig,
            },
            "total_score": total_score,
            "combined_signature": combined_sig,
            "radar_data": {
                "labels": radar_labels,
                "instrument_values": radar_inst,
                "vocal_values": radar_vocal,
            },
        }

    # ================================================================
    # インストルメント軸スコアリング
    # ================================================================

    def _score_instrument(self, data: dict) -> dict:
        """全インストルメント軸をスコアリング"""
        scores = {}
        for key, axis_def in INSTRUMENT_AXES.items():
            scorer_name = axis_def["scorer"]
            scorer = getattr(self, scorer_name, None)
            if scorer:
                try:
                    scores[key] = scorer(data)
                except Exception:
                    scores[key] = 0
            else:
                scores[key] = 0
        return scores

    def _score_tempo(self, data: dict) -> int:
        """テンポ感: BPM 80-180の範囲をスコア化"""
        tempos = self._collect_feature(data, "tempo")
        if not tempos:
            return 50
        avg = np.mean(tempos)
        # BPMが極端に低い/高いと低スコア、100-150で高スコア
        if 100 <= avg <= 150:
            return min(100, int(70 + (1 - abs(avg - 125) / 25) * 30))
        elif 80 <= avg <= 180:
            return int(40 + (1 - abs(avg - 130) / 50) * 30)
        else:
            return max(10, int(30 - abs(avg - 130) / 10))

    def _score_sparkle(self, data: dict) -> int:
        """キラキラ感: 高域EQ比率 + シンセ/ベル/ピアノ検出"""
        score = 50
        # 高域EQ
        high_eqs = self._collect_timbre(data, "high")
        if high_eqs:
            avg_high = np.mean(high_eqs)
            score += int((avg_high - 0.2) * 150)  # 0.2基準で上下

        # シンセ/ベル/ピアノ検出 (AudioSet instruments)
        sparkle_words = ["synthesizer", "bell", "chime", "piano", "keyboard",
                         "electric piano", "glockenspiel", "vibraphone", "celesta"]
        inst_count = self._count_audioset_labels(data, sparkle_words)
        score += inst_count * 8

        return max(0, min(100, score))

    def _score_beat_stability(self, data: dict) -> int:
        """ビート安定度: ドラムのRMS安定性とリズム規則性"""
        score = 50
        drums = data.get("drums", {})
        if "audio_features" in drums:
            rhythm = drums["audio_features"].get("rhythm_pattern", {})
            regularity = rhythm.get("regularity", 0)
            score = int(regularity * 100)
            # 4つ打ちはさらにボーナス
            if rhythm.get("type") == "Four-on-the-floor":
                score = min(100, score + 15)
        return max(0, min(100, score))

    def _score_pop_affinity(self, data: dict) -> int:
        """Pop適合度: AudioSetのPop/Music系ラベルのスコア"""
        pop_words = ["pop", "happy music", "dance", "disco"]
        score = 30  # ベースライン

        # master_mix優先
        mm = data.get("master_mix", {})
        mm_aset = mm.get("audioset", {})
        if isinstance(mm_aset, dict) and "genres" in mm_aset:
            for g in mm_aset["genres"]:
                label = g["label"].lower()
                for pw in pop_words:
                    if pw in label:
                        score += int(g["score"] * 80)

        # ステム側からも拾う
        total = self._count_audioset_scores(data, pop_words)
        score += int(total * 20)

        return max(0, min(100, score))

    def _score_brightness(self, data: dict) -> int:
        """華やかさ: spectral_centroid + 楽器の多様性"""
        centroids = self._collect_feature(data, "spectral_brightness")
        score = 50
        if centroids:
            avg = np.mean(centroids)
            # centroid > 3000 で明るい、< 1500 で暗い
            score = int(np.clip((avg - 1000) / 40, 10, 100))

        # 検出楽器数が多いほど華やか
        inst_count = self._total_audioset_instrument_count(data)
        score = min(100, score + inst_count * 3)

        return max(0, min(100, score))

    def _score_heaviness(self, data: dict) -> int:
        """重厚感: 低域EQ比率 + ディストーション/メタル検出"""
        score = 30
        low_eqs = self._collect_timbre(data, "low")
        if low_eqs:
            avg_low = np.mean(low_eqs)
            score = int(avg_low * 120)

        heavy_words = ["metal", "distortion", "power chord", "heavy", "rock", "grunge"]
        score += self._count_audioset_labels(data, heavy_words) * 10

        return max(0, min(100, score))

    def _score_electronic(self, data: dict) -> int:
        """電子感: シンセ/ドラムマシン検出率"""
        elec_words = ["synthesizer", "electronic", "techno", "electronica", "drum machine",
                      "dubstep", "trance", "house"]
        score = self._count_audioset_labels(data, elec_words) * 12
        return max(0, min(100, score + 10))

    def _score_organic(self, data: dict) -> int:
        """生演奏感: アコースティック楽器検出 + ダイナミックレンジ"""
        organic_words = ["acoustic", "violin", "cello", "piano", "guitar", "flute",
                         "saxophone", "trumpet", "harp", "string", "orchestra"]
        score = self._count_audioset_labels(data, organic_words) * 10

        # ダイナミックレンジ
        for stem in data.values():
            if isinstance(stem, dict) and "timbre" in stem:
                dr = stem["timbre"].get("spatial", {}).get("dynamic_range", 0)
                if dr > 0.1:
                    score += 15
        return max(0, min(100, score + 10))

    # ================================================================
    # ボーカル軸スコアリング
    # ================================================================

    def _score_vocal(self, data: dict) -> dict:
        """全ボーカル軸をスコアリング"""
        scores = {}
        for key, axis_def in VOCAL_AXES.items():
            scorer_name = axis_def["scorer"]
            scorer = getattr(self, scorer_name, None)
            if scorer:
                try:
                    scores[key] = scorer(data)
                except Exception:
                    scores[key] = 0
            else:
                scores[key] = 0
        return scores

    def _score_voice_brightness(self, data: dict) -> int:
        """声の明るさ: ボーカルのspectral_centroid"""
        v = data.get("vocals", {})
        af = v.get("audio_features", {})
        sc = af.get("spectral_brightness", 0)
        if sc == 0:
            return 50
        # 2000-5000 の範囲で正規化
        return max(0, min(100, int((sc - 1500) / 35)))

    def _score_breathiness(self, data: dict) -> int:
        """息遣い度: spectral_flatness (vocal_style)"""
        v = data.get("vocals", {})
        vs = v.get("vocal_style", {})
        br = vs.get("breathiness", 0)
        # flatness 0.01-0.1 の範囲
        return max(0, min(100, int(br * 1000)))

    def _score_pitch_stability(self, data: dict) -> int:
        """音程安定度: メロディデータのピッチ分散の逆"""
        v = data.get("vocals", {})
        melody = v.get("melody", [])
        if not melody or not isinstance(melody, list):
            return 50

        midi_vals = [m["midi"] for m in melody if "midi" in m]
        if len(midi_vals) < 10:
            return 50

        # 短期的な変動 (隣接フレーム差分) の分散
        diffs = np.diff(midi_vals)
        volatility = float(np.std(diffs))

        # volatility 0 = 完一定 → 100, volatility 5+ = 不安定 → 0
        return max(0, min(100, int(100 - volatility * 20)))

    def _score_register_height(self, data: dict) -> int:
        """声域の高さ: 平均MIDI値"""
        v = data.get("vocals", {})
        melody = v.get("melody", [])
        if not melody or not isinstance(melody, list):
            return 50

        midi_vals = [m["midi"] for m in melody if "midi" in m]
        if not midi_vals:
            return 50

        avg = np.mean(midi_vals)
        # MIDI 48(C3)=低い声, 72(C5)=高い声
        return max(0, min(100, int((avg - 45) * 3.5)))

    def _score_power(self, data: dict) -> int:
        """パワー・声量: ボーカルRMS + ダイナミクス"""
        v = data.get("vocals", {})
        af = v.get("audio_features", {})
        rms = af.get("rms", 0)
        vs = v.get("vocal_style", {})
        dyn = vs.get("dynamics_volatility", 0)

        score = 30
        if rms > 0:
            # RMS 0.01=静か → 20, 0.1=大きい → 80
            score = int(np.clip(rms * 800, 10, 90))
        # ダイナミクスが高い = パワフル
        score += int(dyn * 2000)
        return max(0, min(100, score))

    def _score_lightness(self, data: dict) -> int:
        """軽やかさ: dynamics_volatility の逆 + spectral_brightness"""
        v = data.get("vocals", {})
        vs = v.get("vocal_style", {})
        dyn = vs.get("dynamics_volatility", 0.003)
        af = v.get("audio_features", {})
        sc = af.get("spectral_brightness", 2000)

        # 低ダイナミクス変動 = 軽やか
        lightness = max(0, 1 - dyn * 200)
        # 明るい音色 = 軽やか
        brightness_bonus = max(0, (sc - 2000) / 3000)
        score = int((lightness * 0.7 + brightness_bonus * 0.3) * 100)
        return max(0, min(100, score))

    def _score_vibrato(self, data: dict) -> int:
        """ビブラート強度: ピッチの周期的変動"""
        v = data.get("vocals", {})
        melody = v.get("melody", [])
        if not melody or not isinstance(melody, list) or len(melody) < 20:
            return 30

        midi_vals = [m["midi"] for m in melody if "midi" in m]
        if len(midi_vals) < 20:
            return 30

        # 短区間の周期的変動をcheckする (簡易: 差分の自己相関)
        diffs = np.diff(midi_vals)
        if len(diffs) < 10:
            return 30
        ac = np.correlate(diffs[:100], diffs[:100], mode='full')
        ac = ac[len(ac)//2:]
        if len(ac) > 5 and ac[0] > 0:
            ac = ac / ac[0]
            # lag 3-8 あたりにピークがあればビブラート
            vibrato_peak = float(np.max(ac[3:min(8, len(ac))]))
            return max(0, min(100, int(vibrato_peak * 120)))
        return 30

    def _score_vocal_range(self, data: dict) -> int:
        """音域幅: MIDIノートのrange"""
        v = data.get("vocals", {})
        melody = v.get("melody", [])
        if not melody or not isinstance(melody, list):
            return 30

        midi_vals = [m["midi"] for m in melody if "midi" in m]
        if len(midi_vals) < 5:
            return 30

        note_range = max(midi_vals) - min(midi_vals)
        # 6半音=狭い(20), 24半音=広い(100)
        return max(0, min(100, int(note_range * 4)))

    # ================================================================
    # シグネチャ生成
    # ================================================================

    def _generate_instrument_signature(self, scores: dict, data: dict) -> str:
        """インスト面の特徴を自然言語で記述"""
        parts = []

        # テンポ
        tempos = self._collect_feature(data, "tempo")
        if tempos:
            avg_tempo = np.mean(tempos)
            if avg_tempo > 150:
                parts.append("高速テンポ")
            elif avg_tempo > 120:
                parts.append("アップテンポ")
            elif avg_tempo > 90:
                parts.append("ミドルテンポ")
            else:
                parts.append("スローテンポ")

        # キー情報
        mm = data.get("master_mix", {})
        af = mm.get("audio_features", {})
        key_info = af.get("key", {})
        if key_info:
            parts.append(f"キー: {key_info.get('label', '不明')}")

        # リズム
        drums = data.get("drums", {})
        d_af = drums.get("audio_features", {})
        rhythm = d_af.get("rhythm_pattern", {})
        if rhythm.get("type"):
            parts.append(f"リズム: {rhythm['type']}")

        # 特徴的なスコアを文章化
        if scores.get("sparkle", 0) > 70:
            parts.append("キラキラとした煌びやかなサウンド")
        elif scores.get("heaviness", 0) > 70:
            parts.append("重厚で力強いサウンド")

        if scores.get("electronic", 0) > 70:
            parts.append("電子的・シンセティック")
        elif scores.get("organic", 0) > 70:
            parts.append("生楽器志向のオーガニックサウンド")

        if scores.get("beat_stability", 0) > 80:
            parts.append("安定した規則的ビート")

        return "、".join(parts) if parts else "特徴的なサウンド"

    def _generate_vocal_signature(self, scores: dict, data: dict) -> str:
        """ボーカル面の特徴を自然言語で記述"""
        v = data.get("vocals", {})
        if not v:
            return "ボーカルデータなし"

        parts = []

        # 声域の高さ
        rh = scores.get("register_height", 50)
        if rh > 80:
            parts.append("非常に高い声域（ソプラノ/ファルセット域）")
        elif rh > 65:
            parts.append("高めの声域（女性的/高音ボーカル）")
        elif rh > 45:
            parts.append("中音域")
        elif rh > 25:
            parts.append("低めの声域（アルト/テナー域）")
        else:
            parts.append("低い声域（バリトン/バス域）")

        # 声質の明るさ
        vb = scores.get("voice_brightness", 50)
        if vb > 75:
            parts.append("明るくクリアな声質")
        elif vb > 50:
            parts.append("やや明るい声質")
        elif vb < 25:
            parts.append("ダークで温かみのある声質")

        # 息遣い
        br = scores.get("breathiness", 0)
        if br > 70:
            parts.append("ウィスパー・吐息系ボイス")
        elif br > 40:
            parts.append("適度な息成分を含む柔らかい声")

        # パワー
        pw = scores.get("power", 50)
        if pw > 80:
            parts.append("パワフルで力強い歌唱")
        elif pw < 25:
            parts.append("控えめで繊細な歌唱")

        # 軽やかさ
        lt = scores.get("lightness", 50)
        if lt > 75:
            parts.append("軽やかで弾むような表現")
        elif lt < 25:
            parts.append("重みと深みのある表現")

        # ビブラート
        vib = scores.get("vibrato_intensity", 30)
        if vib > 70:
            parts.append("強いビブラート（演歌/クラシック的）")
        elif vib < 20:
            parts.append("ビブラート控えめ（ストレート発声）")

        # 音域幅
        vr = scores.get("vocal_range", 30)
        if vr > 80:
            parts.append("非常に広い音域を使用")
        elif vr < 20:
            parts.append("狭い音域での淡々とした歌唱")

        # 音程安定度
        ps = scores.get("pitch_stability", 50)
        if ps > 85:
            parts.append("音程が非常に安定")
        elif ps < 30:
            parts.append("ピッチが揺れがち（意図的?）")

        return "、".join(parts) if parts else "標準的なボーカル"

    def _generate_combined_signature(self, inst_scores, vocal_scores, data,
                                      inst_sig, vocal_sig) -> str:
        """
        LLMが読んで具体キャラ・アーティスト名を想起できるレベルの
        詳細統合テキストを生成する。
        """
        lines = []
        lines.append(f"【サウンド特性】 {inst_sig}")
        lines.append(f"【ボーカル特性】 {vocal_sig}")

        # LUFS（マスタリング傾向）
        mm = data.get("master_mix", {})
        mm_af = mm.get("audio_features", {})
        lufs = mm_af.get("lufs")
        if lufs is not None:
            if lufs > -10:
                lines.append("【マスタリング】 音圧が非常に高い（ラウドネスウォー志向）")
            elif lufs > -16:
                lines.append("【マスタリング】 現代的な音圧レベル")
            else:
                lines.append("【マスタリング】 ダイナミクス重視のナチュラルな音圧")

        # ジャンル感 (master_mix AudioSet)
        mm_aset = mm.get("audioset", {})
        if isinstance(mm_aset, dict) and "genres" in mm_aset and mm_aset["genres"]:
            genre_labels = [g["label"] for g in mm_aset["genres"][:5]]
            lines.append(f"【ジャンル検出】 {', '.join(genre_labels)}")

        # 総合印象（スコアパターンから）
        impression = self._derive_impression(inst_scores, vocal_scores)
        if impression:
            lines.append(f"【総合印象】 {impression}")

        return "\n".join(lines)

    def _derive_impression(self, inst: dict, vocal: dict) -> str:
        """スコアの組み合わせパターンから印象テキストを導出"""
        impressions = []

        # アイドル系パターン
        if (vocal.get("voice_brightness", 0) > 65 and
            vocal.get("lightness", 0) > 60 and
            inst.get("sparkle", 0) > 55 and
            inst.get("pop_affinity", 0) > 50):
            impressions.append("アイドルソング / 美少女ゲームOP系の明るくキラキラした楽曲")

        # ロック/メタル系
        if (inst.get("heaviness", 0) > 65 and
            vocal.get("power", 0) > 65):
            impressions.append("力強いロック/メタル系のパワフルな楽曲")

        # エレクトロニカ系
        if inst.get("electronic", 0) > 70:
            impressions.append("電子音楽/EDM系のモダンなサウンド")

        # バラード系
        tempos = []
        for stem in ["drums", "bass", "vocals"]:
            sd = inst  # We don't have raw data here, use scores
        if (inst.get("tempo_energy", 0) < 40 and
            vocal.get("power", 0) > 50 and
            vocal.get("vibrato_intensity", 0) > 50):
            impressions.append("情感豊かなバラード")

        # 宝塚/ボーイッシュパターン
        if (vocal.get("register_height", 50) < 45 and
            vocal.get("power", 0) > 60 and
            vocal.get("voice_brightness", 0) > 50):
            impressions.append("宝塚/ボーイッシュ系の力強く美しい低めボーカル")

        # ウィスパー系
        if vocal.get("breathiness", 0) > 65:
            impressions.append("ウィスパー/ASMR的な囁き系ボーカル")

        # クラシカル
        if (vocal.get("vibrato_intensity", 0) > 70 and
            inst.get("organic", 0) > 60):
            impressions.append("クラシカル/オペラ的な格調高い楽曲")

        return " / ".join(impressions) if impressions else "ユニークな個性を持つ楽曲"

    # ================================================================
    # ユーティリティ (データ収集ヘルパー)
    # ================================================================

    def _collect_feature(self, data: dict, feature_key: str) -> list:
        """全ステムから特定の audio_features 値を収集"""
        values = []
        for stem_name, stem_data in data.items():
            if not isinstance(stem_data, dict):
                continue
            af = stem_data.get("audio_features", {})
            if isinstance(af, dict) and feature_key in af:
                val = af[feature_key]
                if isinstance(val, (int, float)):
                    values.append(val)
        return values

    def _collect_timbre(self, data: dict, band: str) -> list:
        """全ステムから特定帯域のEQバランス値を収集"""
        values = []
        for stem_data in data.values():
            if not isinstance(stem_data, dict):
                continue
            eq = stem_data.get("timbre", {}).get("eq_balance", {})
            if band in eq:
                values.append(eq[band])
        return values

    def _count_audioset_labels(self, data: dict, keywords: list) -> int:
        """全ステム+master_mixの AudioSet から指定キーワードに一致するラベル数を数える"""
        count = 0
        for stem_data in data.values():
            if not isinstance(stem_data, dict):
                continue
            aset = stem_data.get("audioset", {})
            if not isinstance(aset, dict):
                continue
            for bucket in ["genres", "instruments", "effects"]:
                for item in aset.get(bucket, []):
                    label = item.get("label", "").lower()
                    for kw in keywords:
                        if kw in label:
                            count += 1
                            break
        return count

    def _count_audioset_scores(self, data: dict, keywords: list) -> float:
        """AudioSetラベルのスコア合計を返す"""
        total = 0.0
        for stem_data in data.values():
            if not isinstance(stem_data, dict):
                continue
            aset = stem_data.get("audioset", {})
            if not isinstance(aset, dict):
                continue
            for bucket in ["genres", "instruments", "effects"]:
                for item in aset.get(bucket, []):
                    label = item.get("label", "").lower()
                    for kw in keywords:
                        if kw in label:
                            total += item.get("score", 0)
                            break
        return total

    def _total_audioset_instrument_count(self, data: dict) -> int:
        """検出された楽器のユニーク数"""
        instruments = set()
        for stem_data in data.values():
            if not isinstance(stem_data, dict):
                continue
            aset = stem_data.get("audioset", {})
            if isinstance(aset, dict):
                for item in aset.get("instruments", []):
                    instruments.add(item.get("label", "").lower())
        return len(instruments)
