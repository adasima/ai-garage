import os
import json
from .exporter import Exporter

class Summarizer:
    def __init__(self):
        self.exporter = Exporter()

    def load_analysis(self, session_dir):
        """
        セッションディレクトリから解析結果JSONを読み込む
        """
        json_path = os.path.join(session_dir, "analysis_report.json")
        if not os.path.exists(json_path):
            return None
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def summarize(self, session_dir):
        """
        解析結果を読み込み、テキストレポートを返す
        """
        data = self.load_analysis(session_dir)
        if not data:
            return "Analysis report not found."
        
        return self.exporter.generate_report(data)

    def export_midi(self, session_dir):
        """
        解析結果からMIDIファイルを生成し、保存パスを返す
        """
        data = self.load_analysis(session_dir)
        if not data:
            raise FileNotFoundError("Analysis report not found.")
            
        output_path = os.path.join(session_dir, "analysis_score.mid")
        self.exporter.export_midi(data, output_path)
        return output_path
