import datetime
import os
import requests
import subprocess
import tkinter as tk
from threading import Thread
import time

# Variables for directory and camera IP
current_script_dir = os.path.dirname(os.path.abspath(__file__))

def read_camera_ip_from_file():
    with open(os.path.join(current_script_dir, 'IP.txt'), 'r') as f:
        return f.readline().strip()

CAMERA_IP = read_camera_ip_from_file()
CAMERAS = [CAMERA_IP]

running = False
current_session_dir = None

def capture_snapshot():
    global running
    global current_session_dir
    try:
        snapshot_frequency = float(snapshot_entry.get())
    except ValueError:
        snapshot_frequency = 5.0

    while running:
        for CAMERA in CAMERAS:
            camera_base_dir = os.path.join(current_script_dir, "snapshots", CAMERA.replace(".", "_"))
            if not os.path.exists(camera_base_dir):
                os.makedirs(camera_base_dir)
            if current_session_dir is None:
                current_session_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                current_session_dir = os.path.join(camera_base_dir, current_session_time)
                os.makedirs(current_session_dir)
            SNAP = "http://" + CAMERA + "/snap.jpeg"
            response = requests.get(SNAP)
            if response.status_code == 200:
                DATETIME = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                FILENAME = CAMERA.replace(".", "_") + "-" + DATETIME + ".jpeg"
                file_path = os.path.join(current_session_dir, FILENAME)
                with open(file_path, "wb") as f:
                    f.write(response.content)
        time.sleep(snapshot_frequency)

def start_capturing():
    global running
    global current_session_dir
    current_session_dir = None
    running = True
    thread = Thread(target=capture_snapshot)
    thread.start()
    start_button['state'] = 'disabled'
    stop_button['state'] = 'normal'

def stop_capturing():
    global running
    running = False
    start_button['state'] = 'normal'
    stop_button['state'] = 'disabled'
    create_video()

def create_video():
    # Create a list of all jpeg images
    with open(os.path.join(current_session_dir, "filelist.txt"), "w") as f:
        for image in sorted(os.listdir(current_session_dir)):
            if image.endswith(".jpeg"):
                f.write(f"file '{os.path.join(current_session_dir, image)}'\n")

    try:
        framerate = str(int(framerate_entry.get()))
    except ValueError:
        framerate = "60"

    cmd = [
        'ffmpeg', 
        '-r', framerate, 
        '-f', 'concat', 
        '-safe', '0',
        '-i', os.path.join(current_session_dir, "filelist.txt"),
        '-s', '1920x1080', 
        '-vcodec', 'libx264', 
        os.path.join(current_session_dir, 'output.mp4')
    ]
    subprocess.run(cmd)


# GUI
root = tk.Tk()
root.title("UniFi Camera Timelapse")

snapshot_label = tk.Label(root, text="Snapshot Frequency (s):")
snapshot_label.pack(pady=5)
snapshot_entry = tk.Entry(root)
snapshot_entry.pack(pady=5)
snapshot_entry.insert(0, "5")

framerate_label = tk.Label(root, text="Output Video Framerate (fps):")
framerate_label.pack(pady=5)
framerate_entry = tk.Entry(root)
framerate_entry.pack(pady=5)
framerate_entry.insert(0, "60")

start_button = tk.Button(root, text="Start Capturing", command=start_capturing)
start_button.pack(pady=20)

stop_button = tk.Button(root, text="Stop Capturing", command=stop_capturing, state='disabled')
stop_button.pack(pady=20)

root.mainloop()
