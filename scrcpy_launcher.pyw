import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import os
import re

CONFIG_FILE = "scrcpy_config.txt"
scrcpy_process = None  # Global process tracker
scrcpy_path = None


def save_scrcpy_path(path):
    with open(CONFIG_FILE, "w") as f:
        f.write(path)


def load_scrcpy_path():
    global scrcpy_path
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            scrcpy_path = f.read().strip()


def run_scrcpy(args):
    global scrcpy_process
    try:
        if scrcpy_path:
            if sys.platform == "win32":
                scrcpy_process = subprocess.Popen(
                    [scrcpy_path] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,  # Tampilkan output ke log
                )
            else:
                scrcpy_process = subprocess.Popen(
                    [scrcpy_path] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )

            threading.Thread(
                target=read_output, args=(scrcpy_process,), daemon=True
            ).start()
        else:
            messagebox.showwarning("Path Kosong", "Path scrcpy belum diatur.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def read_output(process):
    for line in iter(process.stdout.readline, b""):
        decoded_line = line.decode("utf-8")
        output_box.config(state="normal")
        output_box.insert(tk.END, decoded_line)
        output_box.yview(tk.END)
        output_box.config(state="disabled")


def refresh_devices():
    try:
        result = subprocess.check_output(["adb", "devices"], encoding="utf-8")
        lines = result.strip().split("\n")[1:]
        devices = [line.split("\t")[0] for line in lines if "device" in line]
        device_dropdown["values"] = devices
        if devices:
            selected_device.set(devices[0])
    except Exception as e:
        messagebox.showerror("Error", str(e))


def change_path():
    global scrcpy_path
    path = filedialog.askopenfilename(filetypes=[("Scrcpy Executable", "scrcpy*.exe")])
    if path:
        scrcpy_path = path
        path_label.config(text=f"Scrcpy: {scrcpy_path}")
        save_scrcpy_path(scrcpy_path)


def mirror_usb():
    if not os.path.exists(scrcpy_path):
        messagebox.showerror(
            "Scrcpy Path Error", "Path scrcpy.exe tidak valid atau tidak ditemukan."
        )
        return

    try:
        result = subprocess.check_output(["adb", "devices"], encoding="utf-8")
        lines = result.strip().split("\n")[1:]
        devices = [line.split("\t")[0] for line in lines if "device" in line]
        if not devices:
            messagebox.showwarning(
                "Device Not Found", "Tidak ada device USB yang terdeteksi."
            )
            return
    except Exception as e:
        messagebox.showerror("ADB Error", f"Gagal cek device: {e}")
        return

    args = ["--max-size=1920"]
    if fullscreen_var.get():
        args.append("--fullscreen")
    if always_on_top_var.get():
        args.append("--always-on-top")
    run_scrcpy(args)


def mirror_wifi():
    device = selected_device.get()
    if not device:
        messagebox.showwarning("Warning", "Device belum dipilih.")
        return

    try:
        connect_result = subprocess.run(
            ["adb", "connect", device], capture_output=True, text=True
        )

        if "connected" in connect_result.stdout.lower():
            subprocess.check_output(["adb", "devices", "-l"], encoding="utf-8")
        else:
            messagebox.showerror("Wi-Fi Connect Failed", f"⚠️ Gagal connect ke {device}")
            return

    except Exception as e:
        messagebox.showerror("ADB Connect Error", str(e))
        return

    mirror_usb()


def record_screen():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")]
    )
    if file_path:
        args = ["--record", file_path, "--max-size=1920"]
        if fullscreen_var.get():
            args.append("--fullscreen")
        if always_on_top_var.get():
            args.append("--always-on-top")
        run_scrcpy(args)


def stop_mirroring():
    try:
        result = subprocess.check_output("tasklist", shell=True, encoding="utf-8")
        if "scrcpy.exe" in result:
            subprocess.run("taskkill /f /im scrcpy.exe", shell=True)
        else:
            messagebox.showwarning(
                "Tidak Ada", "⚠️ Tidak ada device yang sedang di-mirror."
            )
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menghentikan mirroring: {e}")


# Main window
root = tk.Tk()
root.title("Scrcpy Launcher")
root.geometry("440x720")
root.resizable(False, False)

# Variables
fullscreen_var = tk.BooleanVar()
always_on_top_var = tk.BooleanVar()
selected_device = tk.StringVar()

# Styles
button_font = ("Segoe UI", 10)
label_font = ("Segoe UI", 11, "bold")

# Title
tk.Label(root, text="SCRCPY LAUNCHER", font=("Segoe UI", 14, "bold")).pack(pady=(15, 5))

# Device Dropdown
tk.Label(root, text="Pilih Device:", font=label_font).pack(pady=(10, 2))
device_dropdown = ttk.Combobox(root, textvariable=selected_device, width=40)
device_dropdown.pack(pady=2)
ttk.Button(root, text="🔄 Refresh Device", command=refresh_devices).pack(pady=(5, 15))

# Path Label
path_label = tk.Label(
    root,
    text=f"Scrcpy: {scrcpy_path or '[Belum diatur]'}",
    wraplength=360,
    anchor="w",
    justify="left",
)
path_label.pack(padx=10)

# Path Button
ttk.Button(root, text="🔧 Ubah Path scrcpy", command=change_path).pack(pady=(5, 15))

# Mirror Buttons
ttk.Button(root, text="📱 Mirror via USB", command=mirror_usb).pack(pady=4)
ttk.Button(root, text="🚶 Mirror via Wi-Fi (auto detect)", command=mirror_wifi).pack(
    pady=4
)

# Checkbox Options
checkbox_frame = tk.Frame(root)
checkbox_frame.pack(pady=10)
tk.Checkbutton(checkbox_frame, text="Fullscreen", variable=fullscreen_var).grid(
    row=0, column=0, padx=10
)
tk.Checkbutton(checkbox_frame, text="Always On Top", variable=always_on_top_var).grid(
    row=0, column=1, padx=10
)

# Record & Stop Buttons
ttk.Button(root, text="⏺️ Record Screen", command=record_screen).pack(pady=(10, 5))
ttk.Button(root, text="🛑 Stop Mirror", command=stop_mirroring).pack(pady=5)

# Log Output Area
tk.Label(root, text="Log Output:", font=label_font).pack(pady=(10, 2))
output_box = ScrolledText(root, height=10, width=55, state="disabled")
output_box.pack(padx=10, pady=5)

# Exit Button
ttk.Button(root, text="❌ Keluar", command=root.quit).pack(pady=(10, 15))

load_scrcpy_path()
root.mainloop()
