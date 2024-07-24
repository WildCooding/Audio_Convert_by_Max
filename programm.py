import tkinter as tk
from tkinter import filedialog, messagebox
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range
import noisereduce as nr
import os
import zipfile
import requests
import shutil

class AudioConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio-Konverter")
        self.root.geometry("600x600")
        self.root.configure(bg='#f0f0f5')
        
        self.base_dir = "C:\\Audio_Convert_by_Max"
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.setup_directories()
        self.ffmpeg_path = self.setup_ffmpeg()

        if self.ffmpeg_path:
            os.environ["PATH"] += os.pathsep + self.ffmpeg_path

        # Dateiauswahl
        self.file_path = None
        self.output_path = None
        self.file_label = tk.Label(root, text="Keine Datei ausgewählt", bg='#f0f0f5', font=('Helvetica', 12))
        self.file_label.pack(pady=20)
        self.select_button = tk.Button(root, text="Audiodatei auswählen", command=self.select_file, bg='#007aff', fg='white', bd=0, relief='ridge', highlightthickness=0, padx=10, pady=5, font=('Helvetica', 12))
        self.select_button.pack(pady=10)
        
        # Optionen
        self.compress_var = tk.IntVar()
        self.noise_gate_var = tk.IntVar()
        self.deecho_var = tk.IntVar()
        
        self.compress_check = tk.Checkbutton(root, text="Komprimieren", variable=self.compress_var, bg='#f0f0f5', font=('Helvetica', 12), command=self.toggle_threshold)
        self.compress_check.pack()
        self.noise_gate_check = tk.Checkbutton(root, text="Rauschen entfernen", variable=self.noise_gate_var, bg='#f0f0f5', font=('Helvetica', 12))
        self.noise_gate_check.pack()
        self.deecho_check = tk.Checkbutton(root, text="Echo entfernen", variable=self.deecho_var, bg='#f0f0f5', font=('Helvetica', 12))
        self.deecho_check.pack()
        
        # Kompressionsthreshold Regler (Initially hidden)
        self.threshold_label = tk.Label(root, text="Kompression Threshold (dB)", bg='#f0f0f5', font=('Helvetica', 12))
        self.threshold_scale = tk.Scale(root, from_=-50, to=0, orient=tk.HORIZONTAL, bg='#f0f0f5', font=('Helvetica', 12))
        self.threshold_scale.set(-20)
        
        # Noise Gate Regler
        self.noise_gate_label = tk.Label(root, text="Noise Gate Schwellenwert (dB)", bg='#f0f0f5', font=('Helvetica', 12))
        self.noise_gate_label.pack()
        self.noise_gate_scale = tk.Scale(root, from_=-60, to=0, orient=tk.HORIZONTAL, bg='#f0f0f5', font=('Helvetica', 12))
        self.noise_gate_scale.set(-32)
        self.noise_gate_scale.pack(pady=10)
        
        # Konvertieren Knopf
        self.convert_button = tk.Button(root, text="In MP3 konvertieren", command=self.convert_to_mp3, bg='#00b050', fg='white', bd=0, relief='ridge', highlightthickness=0, padx=10, pady=5, font=('Helvetica', 12))
        self.convert_button.pack(pady=20)

    def setup_directories(self):
        # Hauptverzeichnis erstellen
        os.makedirs(self.base_dir, exist_ok=True)
        # Temporäres Verzeichnis löschen und neu erstellen
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)

    def setup_ffmpeg(self):
        ffmpeg_dir = os.path.join(self.base_dir, "ffmpeg")
        ffmpeg_bin_path = os.path.join(ffmpeg_dir, 'bin')
        ffmpeg_executable = os.path.join(ffmpeg_bin_path, 'ffmpeg.exe')
        
        if not os.path.exists(ffmpeg_executable):
            try:
                ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                response = requests.get(ffmpeg_url)
                zip_file_path = os.path.join(self.base_dir, "ffmpeg.zip")
                with open(zip_file_path, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(self.base_dir)

                extracted_dir = next(os.walk(self.base_dir))[1][0]
                shutil.move(os.path.join(self.base_dir, extracted_dir), ffmpeg_dir)
                os.remove(zip_file_path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Einrichten von FFmpeg: {e}")
                return None

        return ffmpeg_bin_path

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Audiodateien", "*.wav *.flac *.ogg *.mp4 *.m4a")])
        if self.file_path:
            self.file_label.config(text=self.file_path.split("/")[-1])

    def toggle_threshold(self):
        if self.compress_var.get():
            self.threshold_label.pack(pady=10)
            self.threshold_scale.pack(pady=10)
        else:
            self.threshold_label.pack_forget()
            self.threshold_scale.pack_forget()

    def convert_to_mp3(self):
        if not self.file_path:
            messagebox.showerror("Fehler", "Keine Datei ausgewählt")
            return
        
        if not self.ffmpeg_path or not os.path.isfile(os.path.join(self.ffmpeg_path, 'ffmpeg.exe')):
            messagebox.showerror("Fehler", "FFmpeg nicht gefunden. Konvertierung kann nicht fortgesetzt werden.")
            return

        audio = AudioSegment.from_file(self.file_path)
        
        if self.compress_var.get():
            threshold = self.threshold_scale.get()
            audio = compress_dynamic_range(audio, threshold=threshold)
        if self.noise_gate_var.get():
            noise_threshold = self.noise_gate_scale.get()
            reduced_noise_audio = nr.reduce_noise(y=audio.get_array_of_samples(), sr=audio.frame_rate, prop_decrease=noise_threshold)
            audio = AudioSegment(reduced_noise_audio.tobytes(), frame_rate=audio.frame_rate, sample_width=audio.sample_width, channels=len(audio.split_to_mono()))
        
        self.output_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3-Dateien", "*.mp3")])
        if self.output_path:
            audio.export(self.output_path, format="mp3")
            messagebox.showinfo("Erfolg", f"Datei gespeichert als {self.output_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioConverterApp(root)
    root.mainloop()
