from pynput import keyboard
import tkinter as tk
from tkinter import colorchooser, messagebox
import threading
import time
from collections import defaultdict
import json, os
import sys

# ---------- CONFIG SETUP ----------
CONFIG_PATH = os.path.join(os.path.dirname(sys.executable), "input_viewer_config.json")
DEFAULT_KEYS = ["d", "f", "j", "k", "l"]
DEFAULT_COLORS = ["green", "red", "yellow", "blue", "orange"]

def load_config():
	if os.path.exists(CONFIG_PATH):
		with open(CONFIG_PATH, "r") as f:
			return json.load(f)
	return {k: c for k, c in zip(DEFAULT_KEYS, DEFAULT_COLORS)}

def save_config(config):
	with open(CONFIG_PATH, "w") as f:
		json.dump(config, f)

def show_config_window():
	config = load_config()
	temp_root = tk.Tk()
	temp_root.title("Configure Keys and Colors")
	temp_root.geometry("400x400")

	tk.Label(temp_root, text="Configure keys to monitor and their display colors", font=("Arial", 12, "bold")).pack(pady=10)

	frame = tk.Frame(temp_root)
	frame.pack(pady=5)

	entries = {}
	colors = {}

	def update_button_color(var, btn):
		color = var.get()
		if color.startswith("#") and len(color) == 7:
			btn.config(bg=color, text=color)
		else:
			btn.config(bg="gray", text="Invalid")

	def pick_color(var, btn):
		color = colorchooser.askcolor(color=var.get())[1]
		if color:
			var.set(color)
			update_button_color(var, btn)

	for i, (k, c) in enumerate(config.items()):
		row = tk.Frame(frame)
		row.pack(pady=5, padx=10)

		tk.Label(row, text=f"Key {i+1}:", font=("Arial", 10)).pack(side="left")

		key_var = tk.StringVar(value=k)
		color_var = tk.StringVar(value=c)

		tk.Entry(row, textvariable=key_var, width=5, font=("Consolas", 10)).pack(side="left", padx=5)
		tk.Entry(row, textvariable=color_var, width=10, font=("Consolas", 10)).pack(side="left", padx=5)

		btn = tk.Button(row, text=c, bg=c, font=("Arial", 9),
						command=lambda v=color_var, b=None: pick_color(v, btn))
		btn.pack(side="left", padx=5)

		color_var.trace_add("write", lambda *args, v=color_var, b=btn: update_button_color(v, b))

		entries[i] = key_var
		colors[i] = (color_var, btn)

	def on_save():
		new_conf = {}
		for i in entries:
			k = entries[i].get().strip().lower()
			v = colors[i][0].get().strip()
			if k and v.startswith("#") and len(v) == 7:
				new_conf[k] = v
			elif k and v.lower() in ["red", "blue", "green", "yellow", "orange", "purple"]:
				new_conf[k] = v
			else:
				messagebox.showerror("Invalid Entry", f"Color '{v}' is not valid for key '{k}'.")
				return
		if not new_conf:
			messagebox.showerror("Error", "At least one key-color pair required.")
			return
		save_config(new_conf)
		temp_root.destroy()

	tk.Button(temp_root, text="Save Configuration", font=("Arial", 11), command=on_save).pack(pady=10)
	temp_root.mainloop()

# ---------- SHOW CONFIG WINDOW ----------
show_config_window()
key_color_config = load_config()
WATCH_KEYS = set(key_color_config.keys())

# ---------- MAIN PROGRAM ----------
listener_enabled = True
overlay_visible = True
pressed_keys = set()
total_press_times = []

# GUI setup
root = tk.Tk()
root.title("Input Viewer")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")
root.geometry("600x200+100+400")

labels = {}
key_press_times = defaultdict(list)
font_normal = ("Consolas", 32, "bold")

# Create labels for keys
for i, key in enumerate(key_color_config.keys()):
	lbl = tk.Label(root, text=key.upper(), fg="white", bg="black", font=font_normal, width=2)
	lbl.grid(row=1, column=i, padx=10)
	labels[key] = lbl

# Layout for Space bar
space_label = tk.Label(root, text="Space", fg="white", bg="black", font=font_normal, width=5)
space_label.grid(row=0, column=2)

# Status and IPS label
status_label = tk.Label(root, text="ACTIVE", fg="lime", bg="black", font=("Consolas", 12))
status_label.grid(row=3, column=0, columnspan=5)

ips_label = tk.Label(root, text="0.0 IPS", fg="gray", bg="black", font=("Consolas", 12))
ips_label.grid(row=2, column=2)

def on_press(key):
	global listener_enabled, overlay_visible

	if key == keyboard.Key.f10:
		overlay_visible = not overlay_visible
		if overlay_visible:
			root.deiconify()
		else:
			root.withdraw()
		listener_enabled = overlay_visible
		pressed_keys.clear()
		reset_keys()
		return

	if not listener_enabled:
		return

	try:
		k = key.char.lower()
		if k in WATCH_KEYS and k not in pressed_keys:
			pressed_keys.add(k)
			labels[k].config(bg=key_color_config.get(k, "green"), font=font_normal)
			total_press_times.append(time.time())
	except AttributeError:
		if key == keyboard.Key.space and ' ' not in pressed_keys:
			pressed_keys.add(' ')
			space_label.config(bg="green", font=font_normal)

def on_release(key):
	if not listener_enabled:
		return

	try:
		k = key.char.lower()
		if k in WATCH_KEYS and k in pressed_keys:
			pressed_keys.remove(k)
			labels[k].config(bg="black", font=font_normal)
	except AttributeError:
		if key == keyboard.Key.space and ' ' in pressed_keys:
			pressed_keys.remove(' ')
			space_label.config(bg="black", font=font_normal)

def reset_keys():
	for lbl in labels.values():
		lbl.config(bg="black", font=font_normal)
	space_label.config(bg="black", font=font_normal)

def update_ips():
	while True:
		now = time.time()
		if listener_enabled:
			filtered = [t for t in total_press_times if now - t <= 1.0]
			ips_label.config(text=f"{len(filtered):.1f} IPS")
		else:
			ips_label.config(text="0.0 IPS")
		time.sleep(0.1)

# Start keyboard listener thread
threading.Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).run(), daemon=True).start()
threading.Thread(target=update_ips, daemon=True).start()

# Run GUI
root.mainloop()