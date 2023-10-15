import tkinter as tk
from tkinter import ttk, filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import IPv4Network, IPv4Interface
import os
import subprocess
import time
from threading import Thread, Event
import requests
import webbrowser
import socket

# Configuration
IP_FILE = './IP.txt'
IP_RANGE_FILE = './IP_range.txt'
SNAPSHOT_DIR = './snapshots/'
CHECK_EXTENSION = "/snap.jpeg"
FFMPEG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe')

def get_default_ip_range():
    # Get the IP address of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable, it's just to get the IP address bound to a network interface
        s.connect(('10.254.254.254', 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'
    finally:
        s.close()

    # Assuming a /24 subnet for simplicity
    subnet = IPv4Interface(f'{ip_address}/24').network
    return str(subnet)

def discover_cameras():
    # Try reading from IP.txt first
    if os.path.exists(IP_FILE) and os.path.getsize(IP_FILE) > 0:
        with open(IP_FILE, 'r') as file:
            return [line.strip() for line in file.readlines()]
    else:
        print("IP.txt not found, starting network discovery...")

    # Check if IP_range.txt exists and read the first line for the IP range
    ip_range = get_default_ip_range()
    if os.path.exists(IP_RANGE_FILE):
        with open(IP_RANGE_FILE, "r") as file:
            custom_ip_range = file.readline().strip()
            if custom_ip_range:
                ip_range = custom_ip_range
                print(f"Using IP range from IP_range.txt: {ip_range}")
            else:
                print(f"IP_range.txt is empty. Using detected IP range: {ip_range}")
    else:
        print(f"IP_range.txt not found. Using detected IP range: {ip_range}")

    # Discover cameras on the network using the specified or default IP range
    print("Starting camera discovery...")
    found_cameras = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(check_camera, str(ip)): ip for ip in IPv4Network(ip_range)}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                result = future.result()
                if result:
                    print(f"Discovered camera at {result}")
                    found_cameras.append(result)
            except Exception as exc:
                print(f'{ip} generated an exception: {exc}')
    return found_cameras

def check_camera(ip):
    try:
        response = requests.get(f"http://{ip}{CHECK_EXTENSION}", timeout=1)
        if response.status_code == 200 and response.headers.get('Content-Type') == 'image/jpeg':
            return ip
    except requests.RequestException:
        pass
    return None
class CameraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UniFi Camera Timelapse Creator")

        self.schedule_set = False
        self.schedule_check_active = False
        self.total_captures_var = tk.StringVar()
        self.manual_stop = False
        self.waiting_to_start = False
        self.check_schedule_id = None
        self.blinking_state = False
        self.capturing = Event()
        self.last_printed_schedule = None
        
        # Initialize the attribute
        self.is_schedule_running = False

        # Set minimum window size
        # self.minsize(width=300, height=500)

        # Create the main frame with padding
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(padx=50, pady=20)

        # Now initialize self.total_filesize_var
        self.total_filesize_var = tk.StringVar(self.main_frame, value="Total Filesize: 0MB")
        
        # Internal state
        self.capturing = Event()

        # Initializing counters
        self.start_time = None
        self.total_captures = 0
        self.total_filesize = 0
             
        # Setting up the counters update method to be called every second
        self.after(1000, self.update_counters)

        self.setup_gui()

    def open_github(self, event=None):
        webbrowser.open("https://github.com/inertiacreeping")
              
    def setup_gui(self):
        # Helper function for creating section headers
        def create_section_header(text):
            label = ttk.Label(self.main_frame, text=text, font=("Arial", 12, "bold"), anchor="center")
            label.pack(fill=tk.X, pady=(5, 5), padx=5)
            
        # Section 1: Camera Selection and Setup
        create_section_header("Camera Configuration")
        
        # Camera selection, snapshot frequency, and FPS settings
        camera_heading = ttk.Label(self.main_frame, text="Select your Cameras", font=("Arial", 10, "bold"))
        camera_heading.pack(pady=0)
        explainer_text = ("(You must select a camera(s) before proceeding)")
        label = ttk.Label(self.main_frame, text=explainer_text, wraplength=300)
        label.pack(pady=(0, 0))
        
        # Discover Cameras and Display on GUI
        self.cameras = discover_cameras()
        self.camera_vars = {camera: tk.BooleanVar() for camera in self.cameras}

        for camera, var in self.camera_vars.items():
            chk = tk.Checkbutton(self.main_frame, text=camera, variable=var, command=self.check_cameras_selected)
            chk.pack(pady=0)

        ttk.Label(self.main_frame, text="Snapshot Frequency (s):").pack(pady=5)
        self.snapshot_freq = tk.Entry(self.main_frame)
        self.snapshot_freq.insert(0, "10")  # Default value of 10
        self.snapshot_freq.pack(pady=5)
        
        ttk.Label(self.main_frame, text="Video Frame Rate: (fps)").pack(pady=5)
        self.video_framerate = tk.Entry(self.main_frame)
        self.video_framerate.insert(0, "24")  # Default value of 24
        self.video_framerate.pack(pady=5)

        # Section 2: Immediate Capture Session
        create_section_header("One-Click Start")

        # Adding the explainer text
        explainer_text = ("Once you've selected your cameras above, click the the buttons below to start creating a timelapse immediately.")
        label = ttk.Label(self.main_frame, text=explainer_text, wraplength=300)
        label.pack(pady=(0, 10))
        
        self.start_button = tk.Button(self.main_frame, text="Start Capturing", bg="green", fg="white", font=("Arial", 10, "bold"), state=tk.DISABLED, command=self.start_capture)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.main_frame, text="Stop Capturing", bg="red", fg="white", font=("Arial", 10, "bold"), state=tk.DISABLED, command=self.stop_capture)
        self.stop_button.pack(pady=5)

        # Section 3: Schedule Setup
        create_section_header("Schedule Your Recording")
        explainer_text = ("Or if you prefer to set a schedule, a timelapse will be created every day at the set times. \n\nOnce the schedule has started, clicking \"Stop Schedule\" will stop the schedule and immediately create a timelapse of the captured images. ")
        label = ttk.Label(self.main_frame, text=explainer_text, wraplength=300)
        label.pack(pady=(0, 10))
        
        # Scheduling Widgets
        ttk.Label(self.main_frame, text="Schedule Start", font=("Arial", 10, "bold")).pack(pady=5)

        # Frame for Start Time Dropdowns
        start_frame = tk.Frame(self.main_frame)
        start_frame.pack(pady=2)

        # Hour Dropdown for Start Time
        self.start_hour_var = tk.StringVar(value="08")  # Default value set to 08 for 8am
        self.start_hour_dropdown = ttk.Combobox(start_frame, textvariable=self.start_hour_var, values=[str(i).zfill(2) for i in range(1, 13)], width=3)
        self.start_hour_dropdown.grid(row=0, column=0, padx=5)

        # Minute Dropdown for Start Time
        self.start_minute_var = tk.StringVar(value="00")
        self.start_minute_dropdown = ttk.Combobox(start_frame, textvariable=self.start_minute_var, values=[str(i).zfill(2) for i in range(60)], width=3)
        self.start_minute_dropdown.grid(row=0, column=1, padx=5)

        # AM/PM Dropdown for Start Time
        self.start_ampm_var = tk.StringVar(value="AM")
        self.start_ampm_dropdown = ttk.Combobox(start_frame, textvariable=self.start_ampm_var, values=["AM", "PM"], width=3)
        self.start_ampm_dropdown.grid(row=0, column=2, padx=5)

        ttk.Label(self.main_frame, text="Schedule End", font=("Arial", 10, "bold")).pack(pady=5)

        # Frame for End Time Dropdowns
        end_frame = tk.Frame(self.main_frame)
        end_frame.pack(pady=2)

        # Hour Dropdown for End Time
        self.end_hour_var = tk.StringVar(value="05")  # Default value set to 05 for 5pm
        self.end_hour_dropdown = ttk.Combobox(end_frame, textvariable=self.end_hour_var, values=[str(i).zfill(2) for i in range(1, 13)], width=3)
        self.end_hour_dropdown.grid(row=0, column=0, padx=5)

        # Minute Dropdown for End Time
        self.end_minute_var = tk.StringVar(value="00")
        self.end_minute_dropdown = ttk.Combobox(end_frame, textvariable=self.end_minute_var, values=[str(i).zfill(2) for i in range(60)], width=3)
        self.end_minute_dropdown.grid(row=0, column=1, padx=5)

        # AM/PM Dropdown for End Time
        self.end_ampm_var = tk.StringVar(value="PM")
        self.end_ampm_dropdown = ttk.Combobox(end_frame, textvariable=self.end_ampm_var, values=["AM", "PM"], width=3)
        self.end_ampm_dropdown.grid(row=0, column=2, padx=5)

        self.schedule_status_var = tk.StringVar(self.main_frame, value="Schedule: Not Running")
        self.schedule_status_label = ttk.Label(self.main_frame, textvariable=self.schedule_status_var)
        self.schedule_status_label.pack(pady=5)

        # Here's where the magic happens
        # Changing the initial button text to "Start Schedule"
        # Also, let's set its default state to DISABLED, shall we?
        self.schedule_button = tk.Button(self.main_frame, text="Start Schedule", bg="yellow", fg="black", font=("Arial", 10, "bold"), state=tk.DISABLED, command=self.toggle_schedule)
        self.schedule_button.pack(pady=5)

        # Section 4: Incremental Counters
        create_section_header("Previous Session Metrics")
        
        # Adding GUI elements for counters
        self.elapsed_time_var = tk.StringVar(self.main_frame, value="Elapsed Time: 0s")
        ttk.Label(self.main_frame, textvariable=self.elapsed_time_var).pack(pady=0)

        self.captures_var = tk.StringVar(self.main_frame, value="Total Captures: 0")
        ttk.Label(self.main_frame, textvariable=self.captures_var).pack(pady=0)

        self.filesize_var = tk.StringVar(self.main_frame, value="Total Filesize: 0MB")
        ttk.Label(self.main_frame, textvariable=self.filesize_var).pack(pady=0)

        self.video_length_var = tk.StringVar(self.main_frame, value="Estimated Video Length: 0s")
        ttk.Label(self.main_frame, textvariable=self.video_length_var).pack(pady=0)

        # Section 5: Convert Existing Images
        create_section_header("Convert Stored Snapshots")
        explainer_text = ("Click the button below and select a folder with previously captured images.")
        label = ttk.Label(self.main_frame, text=explainer_text, wraplength=300)
        label.pack(pady=(0, 0))

        # Convert Existing Images Button
        self.convert_button = tk.Button(self.main_frame, text="Convert Existing Images", command=self.convert_existing_images)
        self.convert_button.pack(pady=10)

        github_link = ttk.Label(self.main_frame, 
                                text="Visit My GitHub", 
                                font=("Arial", 8, "underline"),
                                foreground="blue",
                                cursor="hand2") # Changes the cursor when you hover over it
        github_link.bind("<Button-1>", self.open_github)
        github_link.pack(side=tk.BOTTOM)

        disclaimer_label = ttk.Label(self.main_frame, 
                                     text="This code can only be used with a non-commercial license.",
                                     font=("Arial", 8))
        disclaimer_label.pack(side=tk.BOTTOM)

        copyright_label = ttk.Label(self.main_frame, 
                            text="© Morris Lazootin 2023", 
                            font=("Arial", 8))
        copyright_label.pack(side=tk.BOTTOM)

    def toggle_schedule(self):
        # Oh, look who's trying to start the schedule!
        if not hasattr(self, 'is_schedule_running') or not self.is_schedule_running:
            # Convert 12-hour format to 24-hour format, because apparently we like math
            start_hour_24 = int(self.start_hour_var.get())
            if self.start_ampm_var.get() == "PM" and start_hour_24 != 12:
                start_hour_24 += 12
            elif self.start_ampm_var.get() == "AM" and start_hour_24 == 12:
                start_hour_24 = 0

            end_hour_24 = int(self.end_hour_var.get())
            if self.end_ampm_var.get() == "PM" and end_hour_24 != 12:
                end_hour_24 += 12
            elif self.end_ampm_var.get() == "AM" and end_hour_24 == 12:
                end_hour_24 = 0

            # Setting up the schedule times, because time waits for no one
            self.start_time_schedule = f"{start_hour_24:02}:{self.start_minute_var.get()}"
            self.end_time_schedule = f"{end_hour_24:02}:{self.end_minute_var.get()}"

            # Change the background color of start and stop buttons to grey
            self.start_button.config(state=tk.DISABLED, bg="grey")
            self.stop_button.config(state=tk.DISABLED, bg="grey")
            self.convert_button.config(state=tk.DISABLED)

            # Look at you, turning the schedule on!
            self.is_schedule_running = True
            self.schedule_status_var.set("Schedule is active. Waiting to start capturing...")
            self.schedule_status_label.config(foreground="red", font=("Arial", 10, "bold"))
            self.schedule_button.config(text="Stop Schedule", bg="red", fg="white", font=("Arial", 10, "bold"))
            
            # Reset the manual_stop flag. We're doing things automatically now!
            self.manual_stop = False  

            # Let's keep an eye on the time and see when it's showtime
            self.check_schedule_id = self.after(10000, self.check_schedule)

        # Oh, changed your mind? Stopping the schedule now!
        else:
            # Turning off the schedule, hope you had a good reason!
            self.is_schedule_running = False
            
            # Clear the schedule status label
            self.schedule_status_var.set("")
            self.schedule_status_label.config(foreground="black", font=("Arial", 10))
            if hasattr(self, 'blink_id'):  # Stop blinking
                self.after_cancel(self.blink_id)

            # Change the text and appearance of the schedule button
            self.schedule_button.config(text="Start Schedule", bg="yellow", fg="black", font=("Arial", 10, "bold"))
            self.stop_button.config(state=tk.NORMAL)  # Re-enable the "Stop Capturing" button
                    
            # If capturing is active, we're shutting it down!
            if self.capturing.is_set():
                self.stop_capture()
                    
            # Let's bring back the other buttons, just in case you want to use them
            # Revert the background color of start and stop buttons to their original colors
            self.start_button.config(state=tk.NORMAL, bg="green")
            self.stop_button.config(state=tk.DISABLED, bg="red")
            self.convert_button.config(state=tk.NORMAL)
            
            # Stopping the check_schedule loop, because we're not waiting anymore
            if hasattr(self, 'check_schedule_id'):
                self.after_cancel(self.check_schedule_id)

    def toggle_blink(self):
        if self.is_schedule_running and self.capturing.is_set():
            if self.blinking_state:
                self.schedule_status_label.config(foreground="red")
            else:
                self.schedule_status_label.config(foreground="white")  # set to the background color to hide
            self.blinking_state = not self.blinking_state
            self.after(500, self.toggle_blink)  # Call every 500ms for blinking effect
        else:
            self.schedule_status_label.config(foreground="black")
        
    def check_schedule(self):
        # If the schedule isn't running, don't proceed with the check.
        if not hasattr(self, 'is_schedule_running') or not self.is_schedule_running:
            return
        # Prevent multiple simultaneous invocations of this method
        if hasattr(self, 'is_checking_schedule') and self.is_checking_schedule:
            return

        self.is_checking_schedule = True

        current_time = time.strftime("%H:%M")

        # Only print the schedule if it has changed since the last check
        if not hasattr(self, 'last_printed_schedule') or self.last_printed_schedule != (self.start_time_schedule, self.end_time_schedule):
            print("Current Time:", current_time)
            print("Start Time Schedule:", self.start_time_schedule)
            print("End Time Schedule:", self.end_time_schedule)
            self.last_printed_schedule = (self.start_time_schedule, self.end_time_schedule)

        if current_time >= self.start_time_schedule and current_time <= self.end_time_schedule:
            print("Inside scheduled time.")
            if not self.capturing.is_set() and self.is_schedule_running and not self.manual_stop:
                self.start_capture()
                self.schedule_status_var.set("CURRENTLY RECORDING")
                self.schedule_status_label.config(foreground="red", font=("Arial", 10, "bold"))
                self.toggle_blink()
        else:
            print("Outside scheduled time.")
            if self.capturing.is_set():
                self.stop_capture()
            # Since we're outside the scheduled time, set waiting_to_start to True
            self.waiting_to_start = True
            if self.is_schedule_running:  # Check if the schedule is still active
                self.schedule_status_var.set("Waiting for next scheduled time...")
                self.schedule_status_label.config(foreground="blue", font=("Arial", 10))
                self.toggle_blink()

        # Schedule the next check after 10 seconds (10000 milliseconds) instead of 60 seconds
        self.after(10000, self.check_schedule) 
        self.is_checking_schedule = False
        
    def update_counters(self):
        if self.capturing.is_set() and self.start_time:
            # Update Elapsed Time
            elapsed_seconds = int(time.time() - self.start_time)
            hours, remainder = divmod(elapsed_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed_time_var.set(f"Elapsed Time: {hours}:{minutes:02}:{seconds:02}")

            # Update Captures Counter (based on files created for the current session)
            session_folder = os.path.join(SNAPSHOT_DIR, self.cameras[0], self.session_start_time)  # Assuming all cameras save in the same session folder
            if os.path.exists(session_folder):
                    self.total_captures = len([f for f in os.listdir(session_folder) if f.endswith('.jpeg')])
                    self.total_filesize = sum([os.path.getsize(os.path.join(session_folder, f)) 
                                               for f in os.listdir(session_folder) if f.endswith('.jpeg')]) / (1024 * 1024)  # in MB
            else:
                self.total_captures = 0
                self.total_filesize = 0
                    
            # Update the UI with the new counter values
            self.captures_var.set(f"Total Captures: {self.total_captures}")
            self.filesize_var.set(f"Total Filesize: {self.total_filesize:.2f} MB")
            
            # Update Estimated Video Length
            framerate = int(self.video_framerate.get() or '30')
            estimated_length = self.total_captures / framerate
            minutes, seconds = divmod(estimated_length, 60)
            
            # Formatting the estimated video length
            formatted_length = f"{int(minutes)} Minutes {int(seconds)} Seconds"
        
            self.video_length_var.set(formatted_length)

        # Schedule the next update
        self.after(1000, self.update_counters)

    def check_cameras_selected(self):
        # If any camera is selected, enable the 'Start Schedule' button. Simple!
        for var in self.camera_vars.values():
            if var.get():
                self.start_button.config(state=tk.NORMAL)
                self.schedule_button.config(state=tk.NORMAL)
                return
        self.start_button.config(state=tk.DISABLED)
        self.schedule_button.config(state=tk.DISABLED)

    def start_capture(self):
        # Immediately change the button states
        self.start_button.config(state=tk.DISABLED)
    
        # Check if snapshot_freq is filled, otherwise default to 5 seconds
        try:
            capture_frequency = int(self.snapshot_freq.get())
        except ValueError:
            capture_frequency = 10  # default value

        # If scheduling is active and we're outside the scheduled times, set up to check the schedule
        if hasattr(self, 'is_schedule_running') and self.is_schedule_running:
            current_time = time.strftime("%H:%M")
            if not (self.start_time_schedule <= current_time <= self.end_time_schedule):
                self.waiting_to_start = True
                self.after(1000, self.check_schedule)
                return

        self.begin_capture()

        # Only re-enable the "Stop Capturing" button if the schedule isn't running
        if not (hasattr(self, 'is_schedule_running') and self.is_schedule_running):
            self.stop_button.config(state=tk.NORMAL)

    def begin_capture(self):
        self.capturing.set()
        self.session_start_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Reset counters
        self.start_time = time.time()
        self.total_captures = 0
        self.total_filesize = 0

        # Reset the manual_stop flag
        self.manual_stop = False

        # Check if snapshot_freq is filled, otherwise default to 5 seconds
        try:
            capture_frequency = int(self.snapshot_freq.get())
        except ValueError:
            capture_frequency = 10  # default value
            
        Thread(target=self.capture_images, args=(capture_frequency,)).start()
        
    def capture_images(self, frequency):    
        while self.capturing.is_set():
            for camera, var in self.camera_vars.items():
                if var.get():
                    response = requests.get(f"http://{camera}{CHECK_EXTENSION}")
                    if response.status_code == 200:
                        folder_path = os.path.join(SNAPSHOT_DIR, camera, self.session_start_time)
                        os.makedirs(folder_path, exist_ok=True)
                        with open(os.path.join(folder_path, f"image_{int(time.time())}.jpeg"), 'wb') as f:
                            f.write(response.content)
            time.sleep(frequency)

    def stop_capture(self):
        self.capturing.clear()
        
        # Only update the button states if schedule is not running
        if not hasattr(self, 'is_schedule_running') or not self.is_schedule_running:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

        # Indicate that the recording was stopped manually
        self.manual_stop = True
        
        # Only update the schedule status if the scheduler is running
        if hasattr(self, 'is_schedule_running') and self.is_schedule_running:
            self.schedule_status_var.set("Recording will resume at the next scheduled time")
            self.schedule_status_label.config(foreground="black", font=("Arial", 10))
        
        # Call the convert_images function here
        for camera, var in self.camera_vars.items():
            if var.get():
                folder_path = os.path.join(SNAPSHOT_DIR, camera, self.session_start_time)
                self.convert_images(folder_path, camera)

        # Reset the blinking state and set the label to its original color
        self.blinking_state = False
        self.schedule_status_label.config(foreground="black")
    
    def convert_images(self, folder, camera_ip):
        framerate = self.video_framerate.get() or '24'  # default to 24fps if not provided
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"TIMELAPSE_{camera_ip}_{timestamp}.mp4"

    # Listing all jpeg files in the folder
        image_files = [f for f in os.listdir(folder) if f.endswith('.jpeg')]
        image_files.sort()  # To ensure they are in the order of capture

    # Writing filenames to a temporary txt file
        filelist_path = os.path.join(folder, "filelist.txt")
        with open(filelist_path, 'w') as file:
            for image_file in image_files:
                file.write(f"file '{image_file}'\n")

    # Using FFmpeg's concat demuxer to read the files from the txt file
        command = [
            FFMPEG_PATH,
            '-f', 'concat',
            '-safe', '0',
              '-i', filelist_path,
            '-framerate', framerate,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            os.path.join(folder, output_filename)
        ]
        subprocess.run(command)

    # Deleting the temporary txt file
        os.remove(filelist_path)

    def convert_existing_images(self):
        # Prompt the user to select a directory
        folder_path = filedialog.askdirectory(title="Select Folder Containing Snapshots")
        
        if not folder_path:  # User cancelled the directory selection
            return
        
        # Assuming all cameras save in the same session folder
        # Just taking the first camera as reference for now
        camera_ip = self.cameras[0] if self.cameras else "Unknown_Camera"
        
        # Convert the images to a timelapse video
        self.convert_images(folder_path, camera_ip)

if __name__ == "__main__":
    app = CameraApp()
    app.mainloop()
