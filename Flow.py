import serial
import pyautogui
import tkinter as tk
from tkinter import Toplevel
from threading import Thread
import os
import psutil
import GPUtil
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

# --- CONFIGURATION ---
PORT_SERIE = 'COM5' 
BAUD_RATE = 9600

# --- PALETTE DE COULEURS DYNAMIQUE (Kiana & Miku) ---
COLOR_BG       = "#2E3B55" # Bleu Nuit (Fond)
COLOR_STATS    = "#3E4C6D" # Fond des barres
COLOR_TEXT     = "#FFFFFF" # Blanc
COLOR_ACCENT   = "#85C1E9" # Bleu Miku (Heure/Statut)
COLOR_TEMP_DEF = "#7D67A6" # Violet (Initial)

# HISTORIQUES POUR LES GRAPHIQUES (Analytics)
history_temp = deque([20.0]*150, maxlen=150)
history_hum  = deque([50.0]*150, maxlen=150)

def get_temp_color(temp):
    """ Logique de changement de couleur selon tes palettes """
    if temp <= 18: return "#85C1E9" # Bleu Miku (Froid)
    if temp <= 23: return "#7D67A6" # Violet Kiana (Confort)
    if temp <= 26: return "#F39C12" # Orange Flamescion (Chaud)
    return "#FF4522"                # Rouge Herrscher (Alerte)

# --- INTERFACE GRAPHIQUE ---
root = tk.Tk()
root.title("FLOW Dashboard")
root.geometry("400x520")
root.configure(bg=COLOR_BG)
root.attributes("-topmost", True) # Reste au-dessus des fenêtres

# Titre FLOW centré
label_title = tk.Label(root, text="FLOW", font=("Segoe UI", 26, "bold"), fg=COLOR_TEXT, bg=COLOR_BG)
label_title.pack(pady=(15, 0))

# Horloge Digitale
label_clock = tk.Label(root, text="00:00:00", font=("Segoe UI", 14, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG)
label_clock.pack(pady=5)

# Zone des Capteurs Arduino
sensor_frame = tk.Frame(root, bg=COLOR_BG)
sensor_frame.pack(pady=10, fill="x", padx=20)

# Bloc Température (Dynamique)
temp_box = tk.Frame(sensor_frame, bg=COLOR_TEMP_DEF, padx=10, pady=10)
temp_box.pack(side="left", expand=True, fill="both", padx=5)
label_temp = tk.Label(temp_box, text="--°C", font=("Segoe UI", 26, "bold"), fg="white", bg=COLOR_TEMP_DEF)
label_temp.pack()
label_temp_sub = tk.Label(temp_box, text="TEMPÉRATURE", font=("Segoe UI", 8), fg="white", bg=COLOR_TEMP_DEF)
label_temp_sub.pack()

# Bloc Humidité
hum_box = tk.Frame(sensor_frame, bg="#5DADE2", padx=10, pady=10)
hum_box.pack(side="right", expand=True, fill="both", padx=5)
label_hum = tk.Label(hum_box, text="--%", font=("Segoe UI", 26, "bold"), fg="white", bg="#5DADE2")
label_hum.pack()
tk.Label(hum_box, text="HUMIDITÉ", font=("Segoe UI", 8), fg="white", bg="#5DADE2").pack()

# Monitoring PC (Barres de progression)
pc_frame = tk.Frame(root, bg=COLOR_STATS, pady=15, padx=20)
pc_frame.pack(pady=10, fill="x", padx=20)

def create_bar(parent, text):
    tk.Label(parent, text=text, font=("Segoe UI", 9), fg="white", bg=COLOR_STATS).pack(anchor="w")
    canv = tk.Canvas(parent, width=300, height=8, bg="#25324D", highlightthickness=0)
    canv.pack(pady=(2, 8))
    rect = canv.create_rectangle(0, 0, 0, 8, fill=COLOR_ACCENT, outline="")
    return canv, rect

canv_cpu, rect_cpu = create_bar(pc_frame, "UTILISATION CPU")
canv_ram, rect_ram = create_bar(pc_frame, "MÉMOIRE RAM")
label_gpu = tk.Label(pc_frame, text="GPU LOAD: --%", font=("Segoe UI", 9), fg=COLOR_ACCENT, bg=COLOR_STATS)
label_gpu.pack(anchor="w")

# Barre de statut finale
label_status = tk.Label(root, text="INITIALISATION...", font=("Segoe UI", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG)
label_status.pack(side="bottom", pady=15)

# --- FONCTIONS LOGIQUES ---

def show_graphs():
    """ Affiche la fenêtre Analytics (Bouton 3) """
    try:
        graph_win = Toplevel(root)
        graph_win.title("FLOW - Analytics")
        graph_win.geometry("500x450")
        graph_win.configure(bg=COLOR_BG)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4), facecolor=COLOR_BG)
        fig.subplots_adjust(hspace=0.6)
        
        for ax, data, title, col in zip([ax1, ax2], [history_temp, history_hum], ["Température (°C)", "Humidité (%)"], ["#FF4522", "#5DADE2"]):
            ax.set_facecolor(COLOR_STATS)
            ax.plot(list(data), color=col, linewidth=2)
            ax.set_title(title, color="white", fontsize=10, fontweight='bold')
            ax.tick_params(colors='white', labelsize=8)
            ax.grid(color=COLOR_BG, linestyle='--', alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)
    except Exception as e: print(f"Erreur Graph : {e}")

def update_pc_stats():
    """ Mise à jour des infos Windows """
    try:
        label_clock.config(text=datetime.now().strftime("%H:%M:%S"))
        # CPU & RAM
        cpu_p = psutil.cpu_percent()
        ram_p = psutil.virtual_memory().percent
        canv_cpu.coords(rect_cpu, 0, 0, (cpu_p * 3), 8)
        canv_ram.coords(rect_ram, 0, 0, (ram_p * 3), 8)
        # GPU
        gpus = GPUtil.getGPUs()
        label_gpu.config(text=f"GPU LOAD: {int(gpus[0].load*100)}%" if gpus else "GPU: IDLE")
    except: pass
    root.after(1000, update_pc_stats)

def interpreter(data):
    """ Analyse les messages venant de l'Arduino """
    try:
        if "RFID" in data:
            os.system('rundll32.exe user32.dll,LockWorkStation')
        elif "TEMP" in data:
            val = float(data.split(":")[1])
            c = get_temp_color(val)
            temp_box.config(bg=c)
            label_temp.config(text=f"{val}°C", bg=c)
            label_temp_sub.config(bg=c)
            history_temp.append(val)
        elif "HUM" in data:
            val = float(data.split(":")[1])
            label_hum.config(text=f"{val}%")
            history_hum.append(val)
        elif "IR" in data:
            code = data.split(":")[1].upper().strip()
            if code == "B946FF00": pyautogui.press('volumeup')
            elif code == "EA15FF00": pyautogui.press('volumedown')
            elif code == "E718FF00": os.system("start notion://") # Bouton 2
            elif code == "A15EFF00": show_graphs()                # Bouton 3
    except: pass

def serial_loop():
    """ Connexion série sécurisée avec reconnexion auto """
    while True:
        try:
            with serial.Serial(PORT_SERIE, BAUD_RATE, timeout=1) as ser:
                label_status.config(text="SYSTEM READY", fg=COLOR_ACCENT)
                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line: root.after(10, interpreter, line)
        except:
            label_status.config(text="SEARCHING ARDUINO...", fg="orange")
            time.sleep(5)

# --- LANCEMENT ---
update_pc_stats()
Thread(target=serial_loop, daemon=True).start()
root.mainloop()