import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import numpy as np
import soundfile as sf

# Import the drag and drop wrappers safely
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    print("Please install tkinterdnd2 using: pip install tkinterdnd2")
    sys.exit(1)

class CustomOptionsDialog(tk.Toplevel):
    """Custom unified dialog window to ask user settings right before processing starts."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Batch Processing Options")
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.dest_choice = tk.StringVar(value="new_folder")  
        self.delete_choice = tk.BooleanVar(value=False)
        self.confirmed = False
        
        self.setup_ui()
        self.center_window()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        dest_label = ttk.Label(main_frame, text="Where should the converted mono files be saved?", font=("Arial", 9, "bold"))
        dest_label.pack(anchor="w", pady=(0, 5))
        
        rb_new = ttk.Radiobutton(main_frame, text="Desktop 'Mono_Exports' folder", variable=self.dest_choice, value="new_folder")
        rb_new.pack(anchor="w", padx=10, pady=2)
        
        rb_orig = ttk.Radiobutton(main_frame, text="Same folder as the original file", variable=self.dest_choice, value="original_folder")
        rb_orig.pack(anchor="w", padx=10, pady=2)
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        cb_delete = ttk.Checkbutton(
            main_frame, 
            text="Delete the original false stereo files after successful conversion", 
            variable=self.delete_choice
        )
        cb_delete.pack(anchor="w", pady=(0, 15))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x")
        
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)
        
        btn_start = tk.Button(btn_frame, text="🚀 Start Processing", command=self.on_confirm, bg="#2ca02c", fg="white", font=("Arial", 9, "bold"), padx=10)
        btn_start.pack(side="right", padx=5)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_confirm(self):
        self.confirmed = True
        self.destroy()


class WavMonoSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV False Stereo to Mono Splitter")
        self.root.geometry("650x760")
        self.root.minsize(600, 680)
        
        self.selected_files = []
        self.detection_mode = tk.StringVar(value="tolerance")
        self.last_export_folder = ""  
        
        # UNIVERSAL FIX: Automatically finds standard home desktop paths on both Windows and Mac
        self.output_dir = Path.home() / "Desktop" / "Mono_Exports"
        
        self.setup_ui()
        self.setup_drag_and_drop()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabelframe", padding=10)
        
        drop_frame = ttk.LabelFrame(self.root, text=" 1. Input WAV Files ")
        drop_frame.pack(fill="x", padx=15, pady=5)
        
        self.lbl_drop_prompt = tk.Label(
            drop_frame, 
            text="✨ DRAG & DROP WAV FILES HERE ✨\n— or —", 
            font=("Arial", 10, "bold"), fg="#4a5568", bg="#edf2f7", pady=10, relief="groove"
        )
        self.lbl_drop_prompt.pack(fill="x", padx=5, pady=5)
        
        btn_browse = tk.Button(drop_frame, text="Browse Manually...", command=self.browse_files, bg="#2b88d8", fg="white", font=("Arial", 9, "bold"))
        btn_browse.pack(pady=2)

        list_frame = ttk.LabelFrame(self.root, text=" Selected Processing Queue ")
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=list_scroll.set, font=("Consolas", 9), selectmode="extended")
        list_scroll.config(command=self.file_listbox.yview)
        
        list_scroll.pack(side="right", fill="y")
        self.file_listbox.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.lbl_count = tk.Label(list_frame, text="No files loaded yet", font=("Arial", 9, "italic"))
        self.lbl_count.pack(pady=2, anchor="w", padx=5)

        settings_frame = ttk.LabelFrame(self.root, text=" 2. Detection Sensitivity ")
        settings_frame.pack(fill="x", padx=15, pady=5)
        
        rb_tolerance = tk.Radiobutton(settings_frame, text="Smart Cross-Correlation Mode (Aligns phases, ignores analog modeling dither)", variable=self.detection_mode, value="tolerance")
        rb_tolerance.pack(anchor="w", padx=10, pady=1)
        rb_strict = tk.Radiobutton(settings_frame, text="Strict Mode (Requires absolute 100% bit-for-bit matched data)", variable=self.detection_mode, value="strict")
        rb_strict.pack(anchor="w", padx=10, pady=1)

        log_frame = ttk.LabelFrame(self.root, text=" Progress Log ")
        log_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        self.log_text = tk.Text(log_frame, state="disabled", height=6, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=2)
        
        log_ctrl_frame = ttk.Frame(log_frame)
        log_ctrl_frame.pack(fill="x", pady=2)
        btn_clear_log = ttk.Button(log_ctrl_frame, text="Clear Log Screen", command=self.clear_log_screen)
        btn_clear_log.pack(side="right", padx=5)

        action_button_frame = ttk.Frame(self.root)
        action_button_frame.pack(fill="x", padx=15, pady=10)

        self.btn_process = tk.Button(action_button_frame, text="Analyze & Convert WAVs", command=self.process_files, state="disabled", bg="#2ca02c", fg="white", font=("Arial", 11, "bold"))
        self.btn_process.pack(side="left", fill="x", expand=True, ipady=4)

        self.btn_open_folder = tk.Button(action_button_frame, text="📁 Open Export Folder", command=self.open_destination_folder, state="disabled", bg="#4a5568", fg="white", font=("Arial", 11, "bold"))
        self.btn_open_folder.pack(side="right", padx=(10, 0), ipady=4, ipadx=10)

    def setup_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_dropped_files)
        self.lbl_drop_prompt.drop_target_register(DND_FILES)
        self.lbl_drop_prompt.dnd_bind('<<Drop>>', self.handle_dropped_files)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def clear_log_screen(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def update_queue_status(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.selected_files:
            self.file_listbox.insert(tk.END, f)
            
        if self.selected_files:
            self.lbl_count.config(text=f"📊 {len(self.selected_files)} WAV track(s) loaded inside queue", font=("Arial", 9, "bold"), fg="#2b88d8")
            self.btn_process.config(state="normal")
        else:
            self.lbl_count.config(text="No files loaded yet", font=("Arial", 9, "italic"), fg="black")
            self.btn_process.config(state="disabled")

    def parse_dropped_paths(self, event_data):
        paths = []
        if '{' in event_data:
            import re
            paths = re.findall(r'\{(.*?)\}', event_data)
            cleaned_data = re.sub(r'\{.*?\}', '', event_data)
            paths.extend([p for p in cleaned_data.split() if p])
        else:
            paths = event_data.split()
        return paths

    def handle_dropped_files(self, event):
        raw_paths = self.parse_dropped_paths(event.data)
        added_count = 0
        for path in raw_paths:
            if path.lower().endswith('.wav') and os.path.isfile(path):
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    added_count += 1
        if added_count > 0:
            self.log(f"Loaded {added_count} WAV file(s) via Drag & Drop.")
        self.update_queue_status()

    def browse_files(self):
        file_types = [("WAV Audio Files", "*.wav")]
        files = filedialog.askopenfilenames(title="Select WAV Files", filetypes=file_types)
        if files:
            added_count = 0
            for file in files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    added_count += 1
            if added_count > 0:
                self.log(f"Loaded {added_count} WAV file(s) via Manual Browse.")
            self.update_queue_status()

    def ensure_output_directory(self):
        if not os.path.exists(str(self.output_dir)):
            try:
                os.makedirs(str(self.output_dir), exist_ok=True)
                return True
            except Exception as e:
                self.log(f"Error creating folder: {str(e)}")
                return False
        return True

    def open_destination_folder(self):
        if self.last_export_folder and os.path.exists(self.last_export_folder):
            try:
                if sys.platform == "win32":
                    os.startfile(self.last_export_folder)
                else:
                    import subprocess
                    subprocess.call(["open", self.last_export_folder])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open directory view: {str(e)}")

    def analyze_and_split(self, file_path, target_mode, should_delete):
        file_path = Path(file_path)
        
        if target_mode == "new_folder":
            output_path = self.output_dir / f"{file_path.stem}_mono{file_path.suffix}"
            self.last_export_folder = str(self.output_dir)
        else:
            output_path = file_path.parent / f"{file_path.stem}_mono{file_path.suffix}"
            self.last_export_folder = str(file_path.parent)
            
        try:
            info = sf.info(str(file_path))
            if info.channels < 2:
                return "skipped_already_mono"

            sample_rate = info.samplerate
            subtype = info.subtype

            data, sr = sf.read(str(file_path), always_2d=True)
            left_channel = data[:, 0]
            right_channel = data[:, 1]
            
            is_mono_match = False
            if self.detection_mode.get() == "strict":
                is_mono_match = np.array_equal(left_channel, right_channel)
            else:
                num_samples = len(left_channel)
                start_sample = max(0, num_samples // 4)
                end_sample = min(num_samples, start_sample + (sample_rate * 20)) 
                
                L = left_channel[start_sample:end_sample]
                R = right_channel[start_sample:end_sample]
                
                if np.max(np.abs(L)) > 0.0001 and np.max(np.abs(R)) > 0.0001:
                    correlation_matrix = np.corrcoef(L, R)
                    correlation_coefficient = correlation_matrix[0, 1]
                    
                    if correlation_coefficient > 0.995:
                        is_mono_match = True
                else:
                    is_mono_match = np.array_equal(left_channel, right_channel)

            if is_mono_match:
                sf.write(str(output_path), left_channel, sample_rate, subtype=subtype)
                
                if should_delete:
                    try:
                        os.remove(str(file_path))
                        return "converted_and_deleted"
                    except Exception as ex:
                        self.log(f" -> Warning: Could not delete original {file_path.name}: {str(ex)}")
                return "converted_successfully"
            else:
                return "skipped_true_stereo"
                
        except Exception as e:
            self.log(f" -> Error reading {file_path.name}: {str(e)}")
            return "error"

    def process_files(self):
        dialog = CustomOptionsDialog(self.root)
        self.root.wait_window(dialog)
        
        if not dialog.confirmed:
            self.log("Batch canceled.")
            return
            
        target_mode = dialog.dest_choice.get()
        should_delete = dialog.delete_choice.get()
        
        self.btn_process.config(state="disabled")
        self.btn_open_folder.config(state="disabled")
        self.log("\n--- Starting WAV Processing Batch ---")
        
        if target_mode == "new_folder":
            if not self.ensure_output_directory():
                self.btn_process.config(state="normal")
                return

        converted_list = []
        skipped_stereo_list = []
        skipped_mono_list = []
        error_list = []
        
        files_to_process = list(self.selected_files)
        
        for file in files_to_process:
            filename = Path(file).name
            self.log(f"Processing: {filename}")
            
            result = self.analyze_and_split(file, target_mode, should_delete)
            
            if result in ["converted_successfully", "converted_and_deleted"]:
                del_note = " (Original deleted)" if result == "converted_and_deleted" else ""
                self.log(f" -> MATCH: False Stereo collapsed to Mono{del_note}.")
                converted_list.append(filename)
            elif result == "skipped_true_stereo":
                self.log(" -> SKIPPED: Track contains True Stereo data.")
                skipped_stereo_list.append(filename)
            elif result == "skipped_already_mono":
                self.log(" -> SKIPPED: Source file is already mono.")
                skipped_mono_list.append(filename)
            else:
                error_list.append(filename)

        self.log("\n==================================")
        self.log("       BATCH RUN SUMMARY          ")
        self.log("==================================")
        self.log(f"✅ Successfully Converted: {len(converted_list)}")
        for f in converted_list:
            self.log(f"   • {f}")
            
        if skipped_stereo_list:
            self.log(f"❌ Skipped (True Stereo): {len(skipped_stereo_list)}")
            for f in skipped_stereo_list:
                self.log(f"   • {f}")
                
        if skipped_mono_list:
            self.log(f"ℹ️ Skipped (Already Mono): {len(skipped_mono_list)}")
            
        if error_list:
            self.log(f"⚠️ Errors: {len(error_list)}")
        self.log("==================================\n")
        
        self.selected_files.clear()
        self.update_queue_status()
        
        self.btn_open_folder.config(state="normal", bg="#0056b3")
        
        messagebox.showinfo("Batch Complete", f"Finished processing files!\n\nConverted: {len(converted_list)}\nSkipped: {len(skipped_stereo_list)}")
        self.btn_process.config(state="normal")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = WavMonoSplitterApp(root)
    root.mainloop()
