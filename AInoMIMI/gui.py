import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import json
import shutil
# from modules.pipeline import Pipeline  # Lazy loaded
from modules.summarizer import Summarizer
# from modules.surgeon import MODE_STANDARD, MODE_HYBRID # Defined locally to avoid import

MODE_STANDARD = "standard"
MODE_HYBRID   = "hybrid"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Music Analysis Pipeline - The Critic")
        self.geometry("900x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pipeline = None  # 毎回設定に応じて生成
        self.summarizer = Summarizer()
        self.session_dir = None

        # Output directory settings
        self.output_root = os.path.join(os.getcwd(), "output")
        if not os.path.exists(self.output_root):
            os.makedirs(self.output_root)

        # UI Components
        self.setup_ui()
        self.refresh_library()

    def setup_ui(self):
        # Layout: Grid with 2 columns
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (Library)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.lbl_logo = ctk.CTkLabel(self.sidebar_frame, text="AINOMIMI", font=("Outfit", 20, "bold"))
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=20)

        self.btn_refresh = ctk.CTkButton(self.sidebar_frame, text="Refresh Library", command=self.refresh_library, width=160)
        self.btn_refresh.grid(row=1, column=0, padx=20, pady=10)

        # Scrollable list for songs
        self.library_list = ctk.CTkScrollableFrame(self.sidebar_frame, width=180, label_text="Analyzed Songs")
        self.library_list.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_title = ctk.CTkLabel(self.main_frame, text="Analysis Dashboard", font=("Outfit", 24, "bold"))
        self.lbl_title.pack(pady=10)

        # Input Area + Separation Settings
        self.input_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.input_frame.pack(pady=10, fill="x")
        
        self.lbl_instruction = ctk.CTkLabel(self.input_frame, text="New Analysis", font=("Inter", 14, "bold"))
        self.lbl_instruction.pack(pady=5)
        
        # 分離設定パネル
        self.settings_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.settings_frame.pack(pady=5, padx=10, fill="x")
        
        # 左列: モード選択
        left_col = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        left_col.pack(side="left", padx=10)
        ctk.CTkLabel(left_col, text="分離エンジン", font=("Inter", 11)).pack(anchor="w")
        self.var_sep_mode = ctk.StringVar(value="standard")
        self.combo_mode = ctk.CTkOptionMenu(
            left_col,
            values=["Standard (Demucs 6s)", "Hybrid (Roformer+Demucs)"],
            command=self._on_mode_change,
            width=200
        )
        self.combo_mode.pack(pady=2)
        
        # 右列: 反復ブレンド設定
        right_col = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        right_col.pack(side="left", padx=10)
        self.var_iterative = ctk.BooleanVar(value=False)
        self.chk_iterative = ctk.CTkCheckBox(
            right_col, text="反復ブレンド (Iterative)",
            variable=self.var_iterative, command=self._on_iterative_toggle
        )
        self.chk_iterative.pack(anchor="w")
        self.chk_iterative.configure(state="disabled")  # Hybridモード時のみ有効
        
        self.iter_sub = ctk.CTkFrame(right_col, fg_color="transparent")
        self.iter_sub.pack(anchor="w", pady=2)
        ctk.CTkLabel(self.iter_sub, text="パス数:", font=("Inter", 10)).pack(side="left")
        self.var_passes = ctk.IntVar(value=2)
        self.slider_passes = ctk.CTkSlider(
            self.iter_sub, from_=2, to=4, number_of_steps=2,
            variable=self.var_passes, width=80
        )
        self.slider_passes.pack(side="left", padx=5)
        self.lbl_passes = ctk.CTkLabel(self.iter_sub, text="2", font=("Consolas", 10), width=20)
        self.lbl_passes.pack(side="left")
        self.slider_passes.configure(state="disabled")
        self.var_passes.trace_add("write", lambda *_: self.lbl_passes.configure(text=str(self.var_passes.get())))

        # [NEW] 歌詞精度設定
        self.accuracy_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.accuracy_frame.pack(side="left", padx=10)
        ctk.CTkLabel(self.accuracy_frame, text="歌詞解析精度", font=("Inter", 11)).pack(anchor="w")
        self.var_accuracy = ctk.StringVar(value="Standard (Speed)")
        self.combo_accuracy = ctk.CTkOptionMenu(
            self.accuracy_frame,
            values=["Standard (Speed)", "High (Quality)"],
            width=150
        )
        self.combo_accuracy.pack(pady=2)

        # [NEW] Instrumental Mode
        self.var_instrumental = ctk.BooleanVar(value=False)
        self.chk_instrumental = ctk.CTkCheckBox(
            self.accuracy_frame, text="Instrumental (Skip Vocals)",
            variable=self.var_instrumental, font=("Inter", 11)
        )
        self.chk_instrumental.pack(pady=2, anchor="w")

        self.btn_select = ctk.CTkButton(self.input_frame, text="Select Audio File...", command=self.select_file)
        self.btn_select.pack(pady=8)

        # Active Session Info
        self.lbl_current_session = ctk.CTkLabel(self.main_frame, text="Current Session: None", font=("Consolas", 12))
        self.lbl_current_session.pack(pady=5)
        
        # [NEW] Open Folder Button
        self.btn_open_folder = ctk.CTkButton(self.main_frame, text="Open Output Folder", command=self.open_output_folder, width=120, fg_color="gray")
        self.btn_open_folder.pack(pady=2)

        # Result Actions
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.pack(pady=10)
        
        self.btn_report = ctk.CTkButton(self.action_frame, text="View Report", command=self.show_report, state="disabled", width=140)
        self.btn_report.pack(side="left", padx=10)
        
        self.btn_midi = ctk.CTkButton(self.action_frame, text="Export MIDI", command=self.export_midi, state="disabled", width=140, fg_color="green")
        self.btn_midi.pack(side="left", padx=10)

        self.btn_reset = ctk.CTkButton(self.action_frame, text="Reset & Re-analyze", command=self.reset_analysis, state="disabled", width=140, fg_color="firebrick")
        self.btn_reset.pack(side="left", padx=10)

        # Log Area
        self.log_text = ctk.CTkTextbox(self.main_frame, height=150, corner_radius=10)
        self.log_text.pack(pady=10, fill="x")
        self.log_text.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, fill="x")
        
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
        self.lbl_status.pack(pady=5)

    def refresh_library(self):
        for widget in self.library_list.winfo_children():
            widget.destroy()

        if not os.path.exists(self.output_root):
            return

        dirs = [d for d in os.listdir(self.output_root) if os.path.isdir(os.path.join(self.output_root, d))]
        
        for d in dirs:
            json_path = os.path.join(self.output_root, d, "analysis_report.json")
            if os.path.exists(json_path):
                btn = ctk.CTkButton(
                    self.library_list, 
                    text=d[:20] + "..." if len(d) > 20 else d,
                    command=lambda x=d: self.load_session(x),
                    anchor="w",
                    fg_color="transparent",
                    border_width=1,
                    text_color=("gray10", "gray90")
                )
                btn.pack(pady=2, fill="x")

    def load_session(self, dirname):
        session_path = os.path.join(self.output_root, dirname)
        self.session_dir = session_path
        self.lbl_current_session.configure(text=f"Current: {dirname}")
        self.log(f"Loaded session: {dirname}")
        
        self.btn_report.configure(state="normal")
        self.btn_midi.configure(state="normal")
        self.btn_reset.configure(state="normal")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        
        try:
            with open("latest.log", "a", encoding="utf-8") as f:
                f.write(f"{message}\n")
        except:
            pass

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="音声ファイルを選択",
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac *.m4a"), ("All Files", "*.*")]
        )
        if file_path:
            self.start_processing(file_path)

    def start_processing(self, file_path):
        try:
            with open("latest.log", "w", encoding="utf-8") as f:
                f.write(f"--- Processing started for: {os.path.basename(file_path)} ---\n")
        except:
            pass

        self.log(f"Starting processing: {os.path.basename(file_path)}")
        self.progress_bar.set(0)
        self.lbl_status.configure(text="Processing...")
        
        self.btn_select.configure(state="disabled", text="解析中...")
        self.btn_report.configure(state="disabled")
        self.btn_midi.configure(state="disabled")
        self.btn_reset.configure(state="disabled")

        thread = threading.Thread(target=self.run_pipeline, args=(file_path,), daemon=True)
        thread.start()

    def _on_mode_change(self, choice):
        """分離モード変更時のコールバック"""
        is_hybrid = "Hybrid" in choice
        state = "normal" if is_hybrid else "disabled"
        self.chk_iterative.configure(state=state)
        if not is_hybrid:
            self.var_iterative.set(False)
            self.slider_passes.configure(state="disabled")

    def _on_iterative_toggle(self):
        """反復ブレンドON/OFF切替"""
        state = "normal" if self.var_iterative.get() else "disabled"
        self.slider_passes.configure(state=state)

    def _create_pipeline(self):
        """現在の設定からPipelineインスタンスを生成"""
        from modules.pipeline import Pipeline  # Lazy import
        
        mode_text = self.combo_mode.get()
        sep_mode = MODE_HYBRID if "Hybrid" in mode_text else MODE_STANDARD
        iterative = self.var_iterative.get()
        passes = self.var_passes.get()
        accuracy_text = self.combo_accuracy.get()
        lyrics_accuracy = "High" if "High" in accuracy_text else "Standard"
        is_instrumental = self.var_instrumental.get()
        
        self.log(f"Pipeline config: mode={sep_mode}, iterative={iterative}, passes={passes}, accuracy={lyrics_accuracy}, instrumental={is_instrumental}")
        return Pipeline(
            separation_mode=sep_mode,
            iterative=iterative,
            iterative_passes=passes,
            lyrics_accuracy=lyrics_accuracy,
            is_instrumental=is_instrumental
        )

    def run_pipeline(self, file_path):
        try:
            # 毎回設定に応じてPipelineを生成
            self.pipeline = self._create_pipeline()

            def update_progress(msg):
                self.after(0, lambda: self.log(msg))
                if "Separation finished" in msg:
                    self.after(0, lambda: self.progress_bar.set(0.3))
                elif "Phase 2" in msg:
                    self.after(0, lambda: self.progress_bar.set(0.4))
                elif "BS-Roformer" in msg:
                    self.after(0, lambda: self.progress_bar.set(0.15))
                elif "Demucs" in msg:
                    current = self.progress_bar.get()
                    self.after(0, lambda: self.progress_bar.set(min(current + 0.03, 0.3)))
                elif "Analyzing" in msg:
                    current = self.progress_bar.get()
                    if current < 0.9:
                        self.after(0, lambda: self.progress_bar.set(current + 0.05))

            self.session_dir = self.pipeline.run_pipeline(file_path, update_progress)
            
            self.after(0, lambda: self.log(f"SUCCESS: {self.session_dir}"))
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.lbl_status.configure(text="Complete"))
            
            self.after(0, lambda: self.btn_report.configure(state="normal"))
            self.after(0, lambda: self.btn_midi.configure(state="normal"))
            self.after(0, lambda: self.btn_reset.configure(state="normal"))
            self.after(0, lambda: self.refresh_library())

        except Exception as e:
            self.after(0, lambda: self.log(f"CRITICAL ERROR: {str(e)}"))
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, lambda: self.lbl_status.configure(text="Error occurred"))
        finally:
            self.after(0, lambda: self.btn_select.configure(state="normal", text="ファイルを選択 (MP3/WAV)"))

    def show_report(self):
        if not self.session_dir: return
        try:
            report_text = self.summarizer.summarize(self.session_dir)
            top = ctk.CTkToplevel(self)
            top.title("Analysis Report")
            top.geometry("1400x900")

            # メインを左右分割: テキスト(左) + レーダーチャート(右)
            main_pane = ctk.CTkFrame(top, fg_color="transparent")
            main_pane.pack(fill="both", expand=True, padx=10, pady=10)
            main_pane.grid_columnconfigure(0, weight=3)
            main_pane.grid_columnconfigure(1, weight=2)
            main_pane.grid_rowconfigure(0, weight=1)

            # 左: テキストレポート (WQHD対応: 大きめフォント)
            textbox = ctk.CTkTextbox(main_pane, font=("Cascadia Mono", 14), wrap="word")
            textbox.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
            textbox.insert("0.0", report_text)
            textbox.configure(state="disabled")

            # 右: レーダーチャート
            chart_frame = ctk.CTkFrame(main_pane, fg_color="transparent")
            chart_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

            self._embed_radar_chart(chart_frame)

            top.lift()
            top.focus_force()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _embed_radar_chart(self, parent_frame):
        """matplotlibレーダーチャートをGUIフレームに埋め込む"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np

            # データ読み込み
            json_path = os.path.join(self.session_dir, "analysis_report.json")
            if not os.path.exists(json_path):
                lbl = ctk.CTkLabel(parent_frame, text="No profile data")
                lbl.pack(pady=20)
                return

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            profile = data.get("voice_profile", {})
            if not profile or "error" in profile:
                lbl = ctk.CTkLabel(parent_frame, text="Profile not available")
                lbl.pack(pady=20)
                return

            radar = profile.get("radar_data", {})
            labels = radar.get("labels", [])
            inst_values = radar.get("instrument_values", [])
            vocal_values = radar.get("vocal_values", [])

            if not labels:
                lbl = ctk.CTkLabel(parent_frame, text="No radar data")
                lbl.pack(pady=20)
                return

            # --- レーダーチャート描画 ---
            # インスト軸とボーカル軸を別々のチャートに
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4),
                                            subplot_kw=dict(polar=True))
            fig.patch.set_facecolor("#1a1a2e")

            # インスト軸数とボーカル軸数
            n_inst = len(inst_values)
            n_vocal = len(vocal_values)
            inst_labels = labels[:n_inst]
            vocal_labels = labels[n_inst:]

            self._draw_one_radar(ax1, inst_labels, inst_values, "Instrument", "#00d2ff")
            self._draw_one_radar(ax2, vocal_labels, vocal_values, "Vocal", "#ff6b9d")

            fig.tight_layout(pad=1.0)

            # tkinterに埋め込み
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # シグネチャテキストも表示
            sig = profile.get("combined_signature", "")
            if sig:
                sig_box = ctk.CTkTextbox(parent_frame, height=120, font=("Consolas", 10))
                sig_box.pack(fill="x", pady=(5, 0))
                sig_box.insert("0.0", sig)
                sig_box.configure(state="disabled")

        except ImportError:
            lbl = ctk.CTkLabel(parent_frame, text="matplotlib not installed\npip install matplotlib")
            lbl.pack(pady=20)
        except Exception as e:
            lbl = ctk.CTkLabel(parent_frame, text=f"Chart error: {e}")
            lbl.pack(pady=20)

    def _draw_one_radar(self, ax, labels, values, title, color):
        """単一のレーダーチャートを描画する"""
        import numpy as np
        n = len(labels)
        if n == 0:
            return

        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        values_plot = values + [values[0]]  # 閉じる
        angles += [angles[0]]

        ax.set_facecolor("#16213e")
        ax.plot(angles, values_plot, 'o-', linewidth=2, color=color, markersize=4)
        ax.fill(angles, values_plot, alpha=0.25, color=color)
        ax.set_ylim(0, 100)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=7, color="white",
                           fontfamily=["Yu Gothic", "MS Gothic", "sans-serif"])
        ax.set_yticklabels([])
        ax.set_title(title, size=11, color=color, pad=15,
                     fontfamily=["Yu Gothic", "MS Gothic", "sans-serif"])
        ax.spines['polar'].set_color('gray')
        ax.tick_params(axis='x', colors='white')
        ax.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

    def reset_analysis(self):
        if not self.session_dir: return
        if not messagebox.askyesno("Reset Analysis", "Are you sure you want to delete current results and re-analyze?\nThis cannot be undone."):
            return
        try:
            manifest_path = os.path.join(self.session_dir, "ai_context.json")
            input_file = None
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    input_file = data.get("session_info", {}).get("input_file")
            
            if not input_file:
                messagebox.showerror("Error", "Could not find input file information.")
                return
            if not os.path.exists(input_file):
                messagebox.showerror("Error", f"Original input file not found:\n{input_file}")
                return

            try:
                shutil.rmtree(self.session_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete session directory:\n{e}\n\nPlease delete the folder manually: {self.session_dir}")
                return
            
            self.session_dir = None
            self.lbl_current_session.configure(text="Current: None")
            self.refresh_library()
            self.log(f"Resetting analysis for: {input_file}")
            self.start_processing(input_file)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_midi(self):
        if not self.session_dir: return
        try:
            midi_path = self.summarizer.export_midi(self.session_dir)
            display_path = midi_path.replace("/", "\\")
            messagebox.showinfo("Export Success", f"MIDI file saved to:\n{display_path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
            
    def open_output_folder(self):
        """現在のセッションフォルダ、なければOutputルートを開く"""
        target = self.session_dir if self.session_dir else self.output_root
        if os.path.exists(target):
            os.startfile(target)
        else:
            messagebox.showerror("Error", f"Folder not found: {target}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
