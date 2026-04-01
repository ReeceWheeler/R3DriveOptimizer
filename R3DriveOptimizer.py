import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import psutil
import re
import ctypes
import sys
import os

# ---------------------------
# Admin check
# ---------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

# ---------------------------
# Format GB
# ---------------------------
def format_gb(b):
    return f"{b / (1024**3):.1f} GB"

# ---------------------------
# Get drives
# ---------------------------
def get_drives():
    drive_map = {}
    for p in psutil.disk_partitions():
        if not p.fstype:
            continue
        try:
            usage = psutil.disk_usage(p.mountpoint)
            label = f"{p.device} | {format_gb(usage.total)} | {format_gb(usage.free)} free"
            drive_map[label] = p.device
        except:
            continue
    return drive_map

# ---------------------------
# Extract %
# ---------------------------
def extract_percent(text):
    match = re.search(r"(\d+)%", text)
    return int(match.group(1)) if match else None

# ---------------------------
# Update progress
# ---------------------------
def update_progress(p):
    progress_var.set(p)
    percent_label.config(text=f"Progress: {p}%")

def append_log(text):
    log_box.insert(tk.END, text)
    log_box.see(tk.END)

# ---------------------------
# Defrag
# ---------------------------
def defrag_drive(drive):
    try:
        # Hide CMD window while running defrag
        process = subprocess.Popen(
            ["defrag", drive, "/U", "/O"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        buffer = ""
        while True:
            char = process.stdout.read(1)
            if not char:
                break

            buffer += char
            root.after(0, lambda c=char: append_log(c))

            percent = extract_percent(buffer)
            if percent is not None:
                root.after(0, lambda p=percent: update_progress(p))
                buffer = ""

        process.wait()
        root.after(0, lambda: update_progress(100))
        root.after(0, lambda: append_log("\n[COMPLETE]\n"))

    except Exception as e:
        root.after(0, lambda: append_log(f"\n[ERROR] {e}\n"))

# ---------------------------
# Start defrag
# ---------------------------
def start_defrag():
    selected = drive_var.get()
    if not selected:
        append_log("[!] Select a drive\n")
        return

    drive = drive_map[selected]

    log_box.delete(1.0, tk.END)
    update_progress(0)

    threading.Thread(target=defrag_drive, args=(drive,), daemon=True).start()

# ---------------------------
# Update drive info live
# ---------------------------
def update_drive_info_live():
    selected = drive_var.get()
    if not selected:
        return

    drive = drive_map[selected]
    try:
        usage = psutil.disk_usage(drive)
        info_label.config(text=
            f"Drive: {drive}\n"
            f"Total: {format_gb(usage.total)}\n"
            f"Free: {format_gb(usage.free)}\n"
            f"Used: {format_gb(usage.used)}"
        )
    except Exception as e:
        info_label.config(text=f"Error reading drive: {e}")

    # Schedule next update in 1 second
    root.after(1000, update_drive_info_live)

# ---------------------------
# GUI
# ---------------------------
root = tk.Tk()
root.title("R3 Drive Optimizer")
root.geometry("750x520")
root.configure(bg="black")

# Set EXE icon for taskbar/window
icon_path = os.path.join(os.path.dirname(sys.argv[0]), "Logo.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

FONT = ("Consolas", 11)

tk.Label(root,
         text="R3 Drive Optimizer",
         font=("Consolas", 16, "bold"),
         bg="black", fg="#00ff00").pack(pady=10)

# Style
style = ttk.Style()
style.theme_use("default")
style.configure("Green.TCombobox",
                fieldbackground="black",
                background="black",
                foreground="#00ff00")
style.map('Green.TCombobox',
          fieldbackground=[('readonly', 'black')],
          foreground=[('readonly', '#00ff00')])

# Drives
drive_var = tk.StringVar()
drive_map = get_drives()
drive_dropdown = ttk.Combobox(root,
                              textvariable=drive_var,
                              values=list(drive_map.keys()),
                              state="readonly",
                              font=FONT,
                              style="Green.TCombobox",
                              width=60)
drive_dropdown.pack(pady=5)
if drive_map:
    drive_dropdown.current(0)

# Drive info
info_label = tk.Label(root,
                      text="",
                      bg="black",
                      fg="#00ff00",
                      font=FONT,
                      justify="left")
info_label.pack(pady=10)

# Start button
tk.Button(root,
          text="START",
          command=start_defrag,
          bg="black",
          fg="#00ff00",
          activebackground="black",
          activeforeground="#00ff00",
          highlightbackground="#00ff00",
          highlightcolor="#00ff00",
          highlightthickness=2,
          bd=0,
          font=("Consolas", 12, "bold"),
          padx=15, pady=6).pack(pady=10)

# Progress label
percent_label = tk.Label(root,
                         text="Progress: 0%",
                         bg="black",
                         fg="#00ff00",
                         font=FONT)
percent_label.pack()

# Progress bar
progress_var = tk.IntVar()
style.configure("green.Horizontal.TProgressbar",
                troughcolor="black",
                background="#00ff00")
ttk.Progressbar(root,
                style="green.Horizontal.TProgressbar",
                orient="horizontal",
                length=550,
                mode="determinate",
                variable=progress_var,
                maximum=100).pack(pady=10)

# Log box
log_box = scrolledtext.ScrolledText(root,
                                    bg="black",
                                    fg="#00ff00",
                                    insertbackground="#00ff00",
                                    font=FONT)
log_box.pack(expand=True, fill="both", padx=10, pady=10)

# Credit label
credit_label = tk.Label(root,
                        text="Created by Reece Wheeler\nWebsite: https://r3cloud.co.uk\nGitHub: https://github.com/ReeceWheeler",
                        bg="black",
                        fg="#00ff00",
                        font=("Consolas", 8),
                        justify="right")
credit_label.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

# Start live drive info updates
update_drive_info_live()

root.mainloop()