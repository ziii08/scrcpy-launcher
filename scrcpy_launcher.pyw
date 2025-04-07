import subprocess
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import os
import configparser
import sys

# File konfigurasi untuk menyimpan path scrcpy
CONFIG_FILE = "config.ini"


# Fungsi untuk memuat path scrcpy dari file konfigurasi
def load_scrcpy_path():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        return config.get("Settings", "scrcpy_path", fallback=None)
    return None


# Fungsi untuk menyimpan path scrcpy ke file konfigurasi
def save_scrcpy_path(path):
    config = configparser.ConfigParser()
    config["Settings"] = {"scrcpy_path": path}
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


# Fungsi untuk mendapatkan path scrcpy yang benar, menyesuaikan dengan file exe
def get_scrcpy_path():
    if getattr(sys, "frozen", False):  # Jika dijalankan dari .exe
        application_path = os.path.dirname(sys.executable)
    else:  # Jika dijalankan sebagai script
        application_path = os.path.dirname(__file__)

    return os.path.join(application_path, "scrcpy.exe")


# Path ke scrcpy.exe dan adb.exe
SCRCPY_PATH = load_scrcpy_path()  # Muat path dari file konfigurasi
ADB_PATH = "adb"  # diasumsikan sudah ada di PATH environment
scrcpy_process = None  # untuk nyimpen proses scrcpy


# Fungsi untuk mengatur path scrcpy melalui UI
def set_scrcpy_path():
    global SCRCPY_PATH
    scrcpy_path = filedialog.askopenfilename(
        title="Pilih scrcpy.exe", filetypes=[("Executable files", "*.exe")]
    )
    if scrcpy_path:
        SCRCPY_PATH = scrcpy_path
        save_scrcpy_path(scrcpy_path)
        update_scrcpy_path_display()
        messagebox.showinfo("Success", f"Path scrcpy telah diset ke {scrcpy_path}")


# Fungsi untuk mengupdate label yang menampilkan path scrcpy
def update_scrcpy_path_display():
    if SCRCPY_PATH:
        scrcpy_path_label.config(text=f"Path scrcpy.exe: {SCRCPY_PATH}")
    else:
        scrcpy_path_label.config(text="Path scrcpy.exe belum diset.")


# Fungsi untuk menjalankan scrcpy
def run_scrcpy(args=None):
    global scrcpy_process
    if args is None:
        args = []
    if SCRCPY_PATH:
        if sys.platform == "win32":  # Pastikan hanya untuk Windows
            # Gunakan CREATE_NO_WINDOW untuk menjalankan scrcpy tanpa terminal
            scrcpy_process = subprocess.Popen(
                [SCRCPY_PATH] + args, creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            scrcpy_process = subprocess.Popen([SCRCPY_PATH] + args)
    else:
        messagebox.showerror(
            "Error", "Path scrcpy tidak ditemukan. Silakan set path terlebih dahulu."
        )


def mirror_usb():
    run_scrcpy()


def mirror_wifi():
    result = subprocess.check_output([ADB_PATH, "devices"], encoding="utf-8")
    if "device" in result.strip().split("\n")[-1]:
        run_scrcpy()
    else:
        ip = simpledialog.askstring("Wi-Fi Mirror", "Masukkan IP HP kamu:")
        if ip:
            subprocess.call([ADB_PATH, "connect", ip])
            run_scrcpy()


def record_screen():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")]
    )
    if file_path:
        run_scrcpy(["--record", file_path])


def fullscreen():
    run_scrcpy(["--fullscreen"])


def always_on_top():
    run_scrcpy(["--always-on-top"])


def stop_mirror():
    global scrcpy_process
    try:
        if scrcpy_process and scrcpy_process.poll() is None:
            scrcpy_process.terminate()
            scrcpy_process = None
            messagebox.showinfo("Stopped", "Scrcpy berhasil dihentikan.")
        else:
            subprocess.call(["taskkill", "/f", "/im", "scrcpy.exe"])
            messagebox.showinfo(
                "Stopped", "Tidak ada proses aktif. Tapi task scrcpy dipaksa berhenti."
            )
    except Exception as e:
        messagebox.showerror("Error", f"Gagal stop: {e}")


# UI
root = tk.Tk()
root.title("Scrcpy Launcher")

tk.Label(root, text="SCRCPY LAUNCHER", font=("Arial", 16)).pack(pady=10)

# Jika path scrcpy belum diset, minta pengguna untuk memilih path scrcpy
if SCRCPY_PATH is None:
    messagebox.showinfo("First Time Setup", "Silakan pilih path scrcpy.exe Anda.")
    set_scrcpy_path()

# Tampilkan path scrcpy yang saat ini digunakan
scrcpy_path_label = tk.Label(
    root, text="Path scrcpy.exe belum diset.", font=("Arial", 10)
)
scrcpy_path_label.pack(pady=10)

# Tombol untuk mengubah path scrcpy
tk.Button(root, text="🔧 Ubah Path scrcpy", width=30, command=set_scrcpy_path).pack(
    pady=5
)

tk.Button(root, text="🖥️ Mirror via USB", width=30, command=mirror_usb).pack(pady=5)
tk.Button(
    root, text="📶 Mirror via Wi-Fi (auto detect)", width=30, command=mirror_wifi
).pack(pady=5)
tk.Button(root, text="🎥 Record Screen", width=30, command=record_screen).pack(pady=5)
tk.Button(root, text="🖥️ Fullscreen", width=30, command=fullscreen).pack(pady=5)
tk.Button(root, text="📌 Always On Top Mirror", width=30, command=always_on_top).pack(
    pady=5
)
tk.Button(root, text="⛔ Stop Mirroring", width=30, command=stop_mirror).pack(pady=5)
tk.Button(root, text="❌ Keluar", width=30, command=root.destroy).pack(pady=20)

# Update tampilan path scrcpy setelah aplikasi dimulai
update_scrcpy_path_display()

root.mainloop()
