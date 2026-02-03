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
PORT_SERIE = 'COM5'  # À vérifier dans le gestionnaire de périphériques
BAUD_RATE = 9600

# --- PALETTE DE COULEURS (FLOW Style) ---
COLOR_BG       = "#2E3B55" # Bleu Nuit profond
COLOR_STATS    = "#3E4C6D" # Fond des barres de stats
COLOR_TEXT     = "#FFFFFF" # Blanc pur
COLOR_ACCENT   = "#85C1E9" # Bleu Glacé (Heure & Statut)
COLOR_TEMP_DEF = "#7D67A6" # Violet par défaut

# --- HISTORIQUES POUR GRAPHIQUES ---
# On pré-remplit avec des 0 pour éviter que les graphes ne plantent au démarrage
history_temp = deque([0]*150, maxlen=150)
history_hum  = deque([0]*150, maxlen=150)

# --- LOGIQUE DE COULEUR DYNAMIQUE ---
def get_temp_color(temp):
    """ Change la couleur du widget selon la température """
    if temp <= 18: return "#A9D8F5" # Bleu clair (Froid)
    if temp <= 22: return "#5DADE2" # Bleu standard
    if temp <= 25: return "#7D67A6" # Violet (Confort)
    if temp <= 28: return "#F39C12" # Orange (Chaud)
    return "#FF4522"                # Rouge (Alerte)

# --- INITIALISATION FENÊTRE PRINCIPALE ---
root = tk.Tk()
root.title("FLOW Dashboard")
root.geometry("400x520")
root.configure(bg=COLOR_BG)
root.attributes("-topmost", True) # Reste au dessus des autres fenêtres

# --- UI : TITRE ET HORLOGE ---
label_title = tk.Label(root, text="FLOW", font=("Segoe UI", 26, "bold"), fg=COLOR_TEXT, bg=COLOR_BG)
label_title.pack(pady=(15, 0))

label_clock = tk.Label(root, text="00:00:00", font=("Segoe UI", 14, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG)
label_clock.pack(pady=5)

# --- UI : CAPTEURS ARDUINO ---
sensor_frame = tk.Frame(root, bg=COLOR_BG)
sensor_frame.pack(pady=10, fill="x", padx=20)

# Bloc Température
temp_box = tk.Frame(sensor_frame, bg=COLOR_TEMP_DEF, padx=10, pady=10)
temp_box.pack(side="left", expand=True, fill="both", padx=5)
label_temp = tk.Label(temp_box, text="--°C", font=("Segoe UI", 26, "bold"), fg="white", bg=COLOR_TEMP_DEF)
label_temp.pack()
tk.Label(temp_box, text="TEMPÉRATURE", font=("Segoe UI", 8), fg="white", bg=COLOR_TEMP_DEF).pack()

# Bloc Humidité
hum_box = tk.Frame(sensor_frame, bg="#5DADE2", padx=10, pady=10)
hum_box.pack(side="right", expand=True, fill="both", padx=5)
label_hum = tk.Label(hum_box, text="--%", font=("Segoe UI", 26, "bold"), fg="white", bg="#5DADE2")
label_hum.pack()
tk.Label(hum_box, text="HUMIDITÉ", font=("Segoe UI", 8), fg="white", bg="#5DADE2").pack()

# --- UI : MONITORING PC (BARRES) ---
pc_frame = tk.Frame(root, bg=COLOR_STATS, pady=15, padx=20)
pc_frame.pack(pady=10, fill="x", padx=20)

def create_bar(parent, label_text):
    """ Crée une barre de progression stylisée """
    tk.Label(parent, text=label_text, font=("Segoe UI", 9), fg="white", bg=COLOR_STATS).pack(anchor="w")
    canv = tk.Canvas(parent, width=300, height=8, bg="#25324d", highlightthickness=0)
    canv.pack(pady=(2, 8))
    rect = canv.create_rectangle(0, 0, 0, 8, fill=COLOR_ACCENT, outline="")
    return canv, rect

canv_cpu, rect_cpu = create_bar(pc_frame, "UTILISATION CPU")
canv_ram, rect_ram = create_bar(pc_frame, "MÉMOIRE RAM")
label_gpu = tk.Label(pc_frame, text="GPU LOAD: --%", font=("Segoe UI", 9), fg=COLOR_ACCENT, bg=COLOR_STATS)
label_gpu.pack(anchor="w")

# Pied de page (Statut)
label_status = tk.Label(root, text="INITIALISATION...", font=("Segoe UI", 9, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG)
label_status.pack(side="bottom", pady=15)

# --- FONCTIONS DE MISE À JOUR ---

def show_graphs():
    """ Affiche la fenêtre des graphiques (Bouton 3) """
    try:
        graph_win = Toplevel(root)
        graph_win.title("FLOW - Analytics")
        graph_win.geometry("500x450")
        graph_win.configure(bg=COLOR_BG)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 4), facecolor=COLOR_BG)
        fig.subplots_adjust(hspace=0.6)
        
        # Style des graphiques
        for ax, data, title, col in zip([ax1, ax2], [history_temp, history_hum], ["Température (°C)", "Humidité (%)"], ["#FF4522", "#5DADE2"]):
            ax.set_facecolor(COLOR_STATS)
            ax.plot(list(data), color=col, linewidth=2)
            ax.set_title(title, color="white", fontsize=10, fontweight='bold')
            ax.tick_params(colors='white', labelsize=8)
            ax.grid(color=COLOR_BG, linestyle='--', alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)
    except Exception as e:
        print(f"Erreur Graphique: {e}")

def update_pc_stats():
    """ Boucle de mise à jour des infos Windows (CPU, RAM, GPU, Heure) """
    label_clock.config(text=datetime.now().strftime("%H:%M:%S"))
    
    # Update CPU
    cpu_p = psutil.cpu_percent()
    canv_cpu.coords(rect_cpu, 0, 0, (cpu_p * 3), 8) # 3 pixels par % (largeur 300)
    
    # Update RAM
    ram_p = psutil.virtual_memory().percent
    canv_ram.coords(rect_ram, 0, 0, (ram_p * 3), 8)
    
    # Update GPU
    try:
        gpus = GPUtil.getGPUs()
        label_gpu.config(text=f"GPU LOAD: {int(gpus[0].load*100)}%" if gpus else "GPU: IDLE")
    except: label_gpu.config(text="GPU: N/A")
    
    root.after(1000, update_pc_stats)

def interpreter_donnees(data):
    """ Gère les messages envoyés par l'Arduino """
    try:
        # 1. RFID (Verrouillage)
        if "RFID" in data: 
            os.system('rundll32.exe user32.dll,LockWorkStation')
        
        # 2. TEMPÉRATURE (Couleur dynamique)
        elif "TEMP" in data:
            val = float(data.split(":")[1])
            new_color = get_temp_color(val)
            temp_box.config(bg=new_color)
            label_temp.config(text=f"{val}°C", bg=new_color)
            history_temp.append(val)
        
        # 3. HUMIDITÉ
        elif "HUM" in data:
            val = float(data.split(":")[1])
            label_hum.config(text=f"{val}%")
            history_hum.append(val)
        
        # 4. TÉLÉCOMMANDE IR
        elif "IR" in data:
            code = data.split(":")[1].upper().strip()
            # Commandes Multimédia
            if code == "B946FF00": pyautogui.press('volumeup')     # Vol +
            elif code == "EA15FF00": pyautogui.press('volumedown') # Vol -
            elif code == "BF40FF00": pyautogui.press('space')      # Play/Pause
            elif code == "BC43FF00": pyautogui.press('nexttrack')  # Suivant
            elif code == "BB44FF00": pyautogui.press('prevtrack')  # Précédent
            # Raccourcis Apps
            elif code == "E619FF00": os.system("start spotify")    # Spotify (EQ)
            elif code == "E718FF00": os.system("start notion://")  # Notion (Bouton 2)
            elif code == "A15EFF00": show_graphs()                 # Analytics (Bouton 3)
    except Exception as e:
        print(f"Erreur interprétation : {e}")

def serial_thread():
    """ Thread de lecture série avec reconnexion automatique """
    while True:
        try:
            ser = serial.Serial(PORT_SERIE, BAUD_RATE, timeout=0.1)
            label_status.config(text="SYSTEM READY", fg=COLOR_ACCENT)
            while True:
                if ser.in_waiting > 0:
                    ligne = ser.readline().decode('utf-8').strip()
                    if ligne: root.after(10, interpreter_donnees, ligne)
        except:
            label_status.config(text="SEARCHING ARDUINO...", fg="orange")
            time.sleep(5) # Attend 5s avant de retenter la connexion

# --- LANCEMENT DU DASHBOARD ---
update_pc_stats()
thread = Thread(target=serial_thread, daemon=True)
thread.start()

root.mainloop()