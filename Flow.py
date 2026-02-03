import serial
import serial.tools.list_ports
import pyautogui
import tkinter as tk
from tkinter import Toplevel
from threading import Thread
import os, psutil, time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque

# --- CONFIGURATION ---
BAUD_RATE = 9600
COLOR_BG       = "#2E3B55" # Fond bleu nuit
COLOR_CARD_PC  = "#3E4C6D" # Fond carte monitoring
COLOR_TEXT     = "#FFFFFF"
COLOR_ACCENT   = "#A9D8F5" # Bleu Miku
COLOR_KIANA    = "#7D67A6" # Violet Kiana

history_temp = deque([20.0]*150, maxlen=150)
history_hum  = deque([50.0]*150, maxlen=150)

# --- FONCTION UI POUR BORDS ARRONDIS ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)

# --- INTERFACE ---
root = tk.Tk()
root.title("FLOW")
root.geometry("450x580")
root.configure(bg=COLOR_BG)
root.attributes("-topmost", True)

# Header : FLOW centré et Heure en GRAS
header_frame = tk.Frame(root, bg=COLOR_BG)
header_frame.pack(pady=20, fill="x")

tk.Label(header_frame, text="FLOW", font=("Segoe UI", 32, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack()
label_clock = tk.Label(header_frame, text="00:00:00", font=("Segoe UI", 18, "bold"), fg=COLOR_ACCENT, bg=COLOR_BG)
label_clock.pack()

# --- ZONE CARTES (TEMP & HUMIDITÉ) ---
card_frame = tk.Frame(root, bg=COLOR_BG)
card_frame.pack(pady=10, padx=20, fill="x")

def make_sensor_card(parent, title, color):
    c = tk.Canvas(parent, width=190, height=130, bg=COLOR_BG, highlightthickness=0)
    c.pack(side="left", padx=10, expand=True)
    create_rounded_rect(c, 0, 0, 190, 130, 25, fill=color)
    val_text = c.create_text(95, 55, text="--", font=("Segoe UI", 32, "bold"), fill="white")
    c.create_text(95, 95, text=title, font=("Segoe UI", 12, "bold"), fill="white")
    return c, val_text

canvas_temp, text_temp = make_sensor_card(card_frame, "TEMP", COLOR_KIANA)
canvas_hum, text_hum = make_sensor_card(card_frame, "HUMIDITÉ", "#5DADE2")

# --- ZONE MONITORING (Bords arrondis) ---
monitor_canvas = tk.Canvas(root, width=400, height=150, bg=COLOR_BG, highlightthickness=0)
monitor_canvas.pack(pady=20)
create_rounded_rect(monitor_canvas, 0, 0, 400, 150, 30, fill=COLOR_CARD_PC)

label_cpu = monitor_canvas.create_text(200, 50, text="CPU UTILIZATION: 0.0%", font=("Segoe UI", 11, "bold"), fill="white")
label_ram = monitor_canvas.create_text(200, 90, text="RAM USAGE: 0.0%", font=("Segoe UI", 11, "bold"), fill="white")

label_status = tk.Label(root, text="RECHERCHE ARDUINO...", font=("Segoe UI", 9), fg="orange", bg=COLOR_BG)
label_status.pack(side="bottom", pady=10)

# --- LOGIQUE DE COMMANDE ---
def execute_command(data):
    if "IR:" in data:
        code = data.split(":")[1].strip().upper()
        # Mappage des boutons
        if code == "BA45FF00":   os.system("shutdown /s /t 1")    # Bouton ARRÊT -> Shutdown PC
        elif code == "B946FF00": pyautogui.press('volumeup')      # Vol +
        elif code == "EA15FF00": pyautogui.press('volumedown')    # Vol -
        elif code == "BF40FF00": pyautogui.press('playpause')     # Pause/Play
        elif code == "BC43FF00": pyautogui.press('nexttrack')     # Suivant
        elif code == "BB44FF00": pyautogui.press('prevtrack')     # Avant
        elif code == "E619FF00": os.system("start spotify")       # Bouton EQ -> Spotify
        elif code == "E718FF00": os.system("start notion://")     # Bouton 2 -> Notion
        elif code == "993BFE28": show_graphs()                    # Bouton 3 -> Analytics
        
    elif "RFID" in data:
        os.system('rundll32.exe user32.dll,LockWorkStation')     # Verrouillage session

    elif "TEMP" in data:
        try:
            val = data.split(":")[1]
            canvas_temp.itemconfig(text_temp, text=f"{val}°C")
            history_temp.append(float(val))
        except: pass
    elif "HUM" in data:
        try:
            val = data.split(":")[1]
            canvas_hum.itemconfig(text_hum, text=f"{val}%")
            history_hum.append(float(val))
        except: pass

def show_graphs():
    try:
        graph_win = Toplevel(root)
        graph_win.title("Analytics")
        graph_win.configure(bg=COLOR_BG)
        fig, ax = plt.subplots(figsize=(5, 3), facecolor=COLOR_BG)
        ax.set_facecolor(COLOR_CARD_PC)
        ax.plot(list(history_temp), color=COLOR_ACCENT)
        ax.tick_params(colors='white')
        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack()
    except: pass

def update_ui():
    label_clock.config(text=datetime.now().strftime("%H:%M:%S"))
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    monitor_canvas.itemconfig(label_cpu, text=f"CPU UTILIZATION: {cpu}%")
    monitor_canvas.itemconfig(label_ram, text=f"RAM USAGE: {ram}%")
    root.after(1000, update_ui)

def serial_thread():
    while True:
        try:
            ports = serial.tools.list_ports.comports()
            target = next((p.device for p in ports if any(x in p.description for x in ["Arduino", "USB-Serial", "CH340"])), None)
            if target:
                with serial.Serial(target, BAUD_RATE, timeout=0.01) as ser:
                    ser.flushInput()
                    label_status.config(text=f"CONNECTED: {target}", fg=COLOR_ACCENT)
                    while True:
                        if ser.in_waiting > 0:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line: root.after(0, execute_command, line)
                        else:
                            time.sleep(0.001)
            else:
                label_status.config(text="NO ARDUINO FOUND", fg="orange")
                time.sleep(2)
        except: time.sleep(2)

update_ui()
Thread(target=serial_thread, daemon=True).start()
root.mainloop()