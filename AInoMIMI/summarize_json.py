import json
import os

# 実行スクリプトのディレクトリ基準でパスを解決
base_dir = os.path.dirname(__file__)
json_path = os.path.join(base_dir, "output", "analysis_report.json")

if not os.path.exists(json_path):
    # フォールバック
    json_path = os.path.join("output", "analysis_report.json")
    if not os.path.exists(json_path):
        print("Error: JSON file not found.")
        exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

output_path = os.path.join(base_dir, "summary_output.txt")
with open(output_path, "w", encoding="utf-8") as out:
    def log(msg):
        print(msg)
        out.write(msg + "\n")

    log("=== DRUMS DETAILED ANALYSIS ===")
    if "drums" in data:
        d = data["drums"]
        
        # Audio Features
        if "audio_features" in d:
            af = d["audio_features"]
            log(f"Tempo: {af.get('tempo', 'N/A')}")
            log(f"RMS (Loudness): {af.get('rms', 0):.4f}")
            log(f"Spectral Brightness: {af.get('spectral_brightness', 0):.2f}")
            
        # Timbre
        if "timbre" in d:
            t = d["timbre"]
            eq = t.get("eq_balance", {})
            log(f"EQ Balance: Low={eq.get('low', 0):.2f}, Mid={eq.get('mid', 0):.2f}, High={eq.get('high', 0):.2f}")
            log(f"Character: {t.get('eq_character', 'N/A')}")
            
            spatial = t.get("spatial", {})
            log(f"Spatial: Flatness={spatial.get('spectral_flatness', 0):.4f}, Dynamic Range={spatial.get('dynamic_range', 0):.4f}")
            log(f"Environment: {spatial.get('shout_out', 'N/A')}")
            
    else:
        log("Drums stem not found in analysis report.")


