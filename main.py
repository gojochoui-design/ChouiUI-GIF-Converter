import argparse, json, os, subprocess, sys, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import converter

BG="#111111"; PANEL="#1b1b1b"; BTN="#2a2a2a"; ACTIVE="#3b3b3b"; TEXT="#e2e2e2"; DIM="#989898"; GREEN="#69a34a"
CONFIG_NAME="choui_settings.json"

def settings_path(): return os.path.join(os.path.expanduser("~"), ".choui_gif_converter.json")
def load_settings():
    try:
        with open(settings_path(), encoding="utf-8") as f: return json.load(f)
    except Exception: return {"output_folder": ""}
def save_settings(data):
    with open(settings_path(), "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

class App:
    def __init__(self, root):
        self.root=root; self.gif_path=None; self.output_path=None; self.busy=False; self.settings=load_settings()
        root.title("ChouiUI GIF Converter"); root.configure(bg=BG); root.resizable(False,False); root.geometry("560x690")
        ttk.Style().configure("Dark.Horizontal.TProgressbar", troughcolor=PANEL, background=GREEN)
        tk.Label(root,text="CHOUIUI  •  GIF CONVERTER",bg=BG,fg=TEXT,font=("Segoe UI",16,"bold")).pack(pady=(24,3))
        tk.Label(root,text="Animated inventory for Minecraft Bedrock",bg=BG,fg=DIM,font=("Segoe UI",9)).pack()
        self.select=tk.Button(root,text="SELECT GIF",command=self.select_gif,bg=BTN,fg=TEXT,activebackground=ACTIVE,activeforeground=TEXT,relief="flat",bd=0,font=("Segoe UI",11,"bold")); self.select.pack(pady=(20,8),ipadx=35,ipady=7)
        self.info=tk.Label(root,text="No GIF selected",bg=BG,fg=DIM,font=("Segoe UI",9)); self.info.pack(pady=(0,8))
        self.preview_photo=ImageTk.PhotoImage(Image.new("RGB",(352,332),PANEL),master=root)
        self.preview=tk.Label(root,bg=PANEL,image=self.preview_photo); self.preview.pack(pady=(0,7))
        self.convert=tk.Button(root,text="CONVERT GIF",command=self.convert_gif,bg=GREEN,fg="white",activebackground="#7cb35b",relief="flat",bd=0,font=("Segoe UI",11,"bold")); self.convert.pack(pady=(10,8),ipadx=45,ipady=8); self.convert.configure(state="disabled")
        self.bar=ttk.Progressbar(root,orient="horizontal",length=360,mode="determinate",style="Dark.Horizontal.TProgressbar"); self.bar.pack(pady=(5,5))
        self.status=tk.Label(root,text="Waiting for a GIF",bg=BG,fg=DIM,font=("Segoe UI",8)); self.status.pack()
        settings=tk.LabelFrame(root,text="  SETTINGS  ",bg=BG,fg=DIM,font=("Segoe UI",8),bd=1,relief="groove"); settings.pack(fill="x",padx=55,pady=(17,10))
        self.folder=tk.Label(settings,text=self.folder_text(),bg=BG,fg=DIM,font=("Segoe UI",8),anchor="w"); self.folder.pack(side="left",fill="x",expand=True,padx=8,pady=8)
        tk.Button(settings,text="CHANGE",command=self.choose_folder,bg=BTN,fg=TEXT,activebackground=ACTIVE,relief="flat",bd=0,font=("Segoe UI",8,"bold")).pack(side="right",padx=6,pady=5)
    def folder_text(self): return self.settings.get("output_folder") or "Same folder as GIF"
    def choose_folder(self):
        folder=filedialog.askdirectory(title="Choose output folder")
        if folder: self.settings["output_folder"]=folder; save_settings(self.settings); self.folder.configure(text=folder)
    def select_gif(self):
        path=filedialog.askopenfilename(title="Select GIF",filetypes=[("GIF files","*.gif"),("All files","*.*")])
        if not path:return
        self.gif_path=path; self.info.configure(text=os.path.basename(path)); self.status.configure(text="Reading GIF...")
        threading.Thread(target=self.load_gif,args=(path,),daemon=True).start()
    def load_gif(self,path):
        try:
            info=converter.probe(path); img=converter.preview_first_frame(path)
            self.root.after(0,lambda:self.loaded(info,img))
        except Exception as e: self.root.after(0,lambda:self.status.configure(text="Could not read this GIF"))
    def loaded(self,info,img):
        self.info.configure(text=f"{os.path.basename(self.gif_path)}  •  {info.original_count} frames  •  {info.width}x{info.height}")
        self.preview_photo=ImageTk.PhotoImage(img,master=self.root); self.preview.configure(image=self.preview_photo); self.status.configure(text="Ready"); self.convert.configure(state="normal")
    def convert_gif(self):
        if not self.gif_path or self.busy:return
        self.busy=True; self.convert.configure(state="disabled"); self.select.configure(state="disabled"); self.bar.configure(value=0)
        out=converter.default_output(self.gif_path,self.settings.get("output_folder") or None); threading.Thread(target=self.worker,args=(out,),daemon=True).start()
    def worker(self,out):
        try:
            def progress(done,total): self.root.after(0,lambda:self.bar.configure(maximum=total,value=done))
            info=converter.convert(self.gif_path,out,progress=progress,status=lambda s:self.root.after(0,lambda:self.status.configure(text=s)))
            self.root.after(0,lambda:self.done(out,info))
        except Exception: self.root.after(0,lambda:self.fail())
    def done(self,out,info):
        self.busy=False; self.output_path=out; self.convert.configure(state="normal"); self.select.configure(state="normal"); self.status.configure(text=f"Saved: {os.path.basename(out)}"); messagebox.showinfo("Done",f"Created {os.path.basename(out)}\n{info.frame_count} frames @ {info.fps} fps")
    def fail(self): self.busy=False; self.convert.configure(state="normal"); self.select.configure(state="normal"); self.status.configure(text="Could not convert this GIF"); messagebox.showerror("Conversion failed","Could not convert this GIF")

def run_cli(args): converter.convert(args.cli,args.output or converter.default_output(args.cli,args.folder))
def main():
    p=argparse.ArgumentParser(); p.add_argument("--cli"); p.add_argument("-o","--output"); p.add_argument("--folder"); a=p.parse_args()
    if a.cli: run_cli(a); return
    root=tk.Tk(); App(root); root.mainloop()
if __name__=="__main__": main()
