import argparse
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import converter

BG = "#141414"
PANEL = "#1d1d1d"
BTN = "#2a2a2a"
BTN_HOVER = "#3a3a3a"
BTN_ACTIVE = "#454545"
TEXT = "#c9c9c9"
DIM = "#8a8a8a"
FAINT = "#5a5a5a"
LINE = "#333333"


class App:
    def __init__(self, root):
        self.root = root
        self.gif_path = None
        self.gif_info = None
        self.preview_photo = None
        self.busy = False
        self.output_path = None

        root.title("ChouiUI GIF Converter")
        root.configure(bg=BG)
        root.resizable(False, False)
        root.geometry("560x700")
        root.minsize(560, 700)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Gray.Horizontal.TProgressbar",
                        troughcolor=PANEL,
                        background="#5a5a5a",
                        bordercolor=BG,
                        lightcolor="#5a5a5a",
                        darkcolor="#5a5a5a")

        header = tk.Label(root, text="ChouiUI GIF Converter", bg=BG, fg=TEXT,
                          font=("Segoe UI", 15, "bold"))
        header.pack(pady=(22, 2))
        sub = tk.Label(root, text="GIF  ->  Bedrock animated inventory  (.mcpack)\nChouiUI Java 1.8.9 UI template",
                       bg=BG, fg=DIM, font=("Segoe UI", 9), justify="center")
        sub.pack()

        self.select_btn = self.make_button(root, "SELECT GIF", self.on_select)
        self.select_btn.pack(pady=(16, 6), ipadx=30, ipady=4)

        self.info = tk.Label(root, text="No GIF selected", bg=BG, fg=DIM,
                             font=("Segoe UI", 9), justify="center")
        self.info.pack(pady=(2, 8))

        self.preview_photo = ImageTk.PhotoImage(
            Image.new("RGB", (352, 332), PANEL), master=root)
        self.preview = tk.Label(root, bg=PANEL, image=self.preview_photo)
        self.preview.pack(pady=(0, 6))
        note = tk.Label(root, text="Max 11 frames (auto-resampled) - 2x render like Java HD packs\nBlack slot lines only, no panel fill - fresh UUIDs every conversion",
                        bg=BG, fg=FAINT, font=("Segoe UI", 8))
        note.pack()

        self.convert_btn = self.make_button(root, "CONVERT", self.on_convert)
        self.convert_btn.pack(pady=(14, 4), ipadx=60, ipady=6)
        self.convert_btn.configure(state="disabled")

        self.bar = ttk.Progressbar(root, orient="horizontal", length=360,
                                   mode="determinate", style="Gray.Horizontal.TProgressbar")
        self.bar.pack(pady=(10, 4))

        self.status = tk.Label(root, text="Waiting for GIF...", bg=BG, fg=DIM,
                               font=("Segoe UI", 8), wraplength=500)
        self.status.pack(pady=(0, 4))

        self.open_btn = self.make_button(root, "OPEN FOLDER", self.on_open_folder)
        self.open_btn.pack(pady=(2, 16), ipadx=24, ipady=3)
        self.open_btn.configure(state="disabled")

    def make_button(self, parent, text, command):
        b = tk.Button(parent, text=text, command=command,
                      bg=BTN, fg=TEXT, activebackground=BTN_ACTIVE, activeforeground=TEXT,
                      relief="flat", bd=0, cursor="hand2",
                      font=("Segoe UI", 10, "bold"), disabledforeground=FAINT)
        b.bind("<Enter>", lambda e: b.configure(bg=BTN_HOVER) if str(b["state"]) == "normal" else None)
        b.bind("<Leave>", lambda e: b.configure(bg=BTN) if str(b["state"]) == "normal" else None)
        return b

    def set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.convert_btn.configure(state=state)
        self.select_btn.configure(state=state)
        if not busy and self.gif_path:
            self.convert_btn.configure(state="normal")

    def on_select(self):
        path = filedialog.askopenfilename(
            title="Select a GIF",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")])
        if not path:
            return
        self.gif_path = path
        self.info.configure(text="Reading GIF...", fg=DIM)
        self.status.configure(text="Loading preview...")
        self.preview.configure(text="loading preview...")
        self.set_busy(False)
        self.convert_btn.configure(state="disabled")
        threading.Thread(target=self._load_gif_worker, args=(path,), daemon=True).start()

    def _load_gif_worker(self, path):
        try:
            info = converter.probe(path)
            img = converter.preview_first_frame(path)
            self.root.after(0, self._load_gif_done, path, info, img, None)
        except Exception as e:
            self.root.after(0, self._load_gif_done, path, None, None, str(e))

    def _load_gif_done(self, path, info, img, error):
        if error is not None:
            self.gif_path = None
            self.gif_info = None
            self.info.configure(text="Could not read GIF: %s" % error, fg=FAINT)
            self.status.configure(text="Waiting for GIF...")
            self.preview_photo = ImageTk.PhotoImage(
                Image.new("RGB", (352, 332), PANEL), master=self.root)
            self.preview.configure(image=self.preview_photo)
            self.convert_btn.configure(state="disabled")
            return
        self.gif_info = info
        name = os.path.basename(path)
        lines = "%s\n%d frames used   |   %d x %d px   |   %d fps" % (
            name, info.frame_count, info.width, info.height, info.fps)
        if info.resampled:
            lines += "\n(resampled from %d original frames)" % info.original_count
        self.info.configure(text=lines, fg=DIM)
        self.preview_photo = self._to_photo(img)
        self.preview.configure(image=self.preview_photo)
        self.status.configure(text="Ready to convert")
        if not self.busy:
            self.convert_btn.configure(state="normal")

    def _to_photo(self, img):
        big = img.resize((352, 332), Image.NEAREST)
        return ImageTk.PhotoImage(big, master=self.root)

    def on_convert(self):
        if not self.gif_path or self.busy:
            return
        out = converter.default_output(self.gif_path)
        self.set_busy(True)
        self.bar.configure(value=0)
        self.open_btn.configure(state="disabled")
        threading.Thread(target=self._convert_worker, args=(self.gif_path, out), daemon=True).start()

    def _convert_worker(self, gif_path, out_path):
        def progress(done, total):
            self.root.after(0, self._set_progress, done, total)

        def status(text):
            self.root.after(0, lambda t=text: self.status.configure(text=t))

        try:
            info = converter.convert(gif_path, out_path, progress=progress, status=status)
            self.root.after(0, self._convert_done, out_path, info, None)
        except Exception as e:
            self.root.after(0, self._convert_done, None, None, str(e))

    def _set_progress(self, done, total):
        self.bar.configure(maximum=max(total, 1), value=done)

    def _convert_done(self, out_path, info, error):
        self.set_busy(False)
        if error is not None:
            self.status.configure(text="Error: %s" % error)
            messagebox.showerror("Conversion failed", error)
            return
        self.output_path = out_path
        self.status.configure(text="Done: %s" % out_path, fg=DIM)
        self.open_btn.configure(state="normal")
        messagebox.showinfo("Converted",
                            "Pack created:\n%s\n\n%d frames @ %d fps" %
                            (out_path, info.frame_count, info.fps))

    def on_open_folder(self):
        if not self.output_path:
            return
        folder = os.path.dirname(os.path.abspath(self.output_path))
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass


def run_cli(args):
    def progress(done, total):
        pct = int(100.0 * done / max(total, 1))
        sys.stdout.write("\rconverting: %d%%" % pct)
        sys.stdout.flush()

    def status(text):
        print(text)

    info = converter.convert(args.cli, args.output or converter.default_output(args.cli),
                             progress=progress, status=status)
    print("")
    print("frames used: %d | fps: %d | resampled: %s" % (
        info.frame_count, info.fps, info.resampled))


def main():
    parser = argparse.ArgumentParser(description="ChouiUI GIF Converter")
    parser.add_argument("--cli", metavar="GIF", help="convert a GIF without opening the GUI")
    parser.add_argument("-o", "--output", metavar="MCPACK", help="output .mcpack path")
    args = parser.parse_args()
    if args.cli:
        run_cli(args)
        return
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
