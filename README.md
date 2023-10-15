# UniFi Camera Timelapse Creator

This script provides a GUI to create timelapses from UniFi Cameras. It discovers cameras on your local network, captures snapshots based on a specified frequency, and then compiles them into a timelapse video.

## Features:
- Discover UniFi Cameras on your network.
- Configure capture settings like snapshot frequency and video frame rate.
- One-click start for immediate timelapse creation.
- Schedule recordings to automatically create a timelapse during specific intervals.
- View metrics from the previous session, such as elapsed time, total captures, and estimated video length.
- Convert previously stored snapshots into a timelapse video.

## Prerequisites:
1. [Python 3](https://www.python.org/downloads/)
2. [Tkinter](https://docs.python.org/3/library/tkinter.html) - For the GUI.
3. [Requests](https://docs.python-requests.org/en/master/) - For making HTTP requests to the cameras.
4. [FFmpeg](https://ffmpeg.org/download.html) - For converting images to video. System-wide or local install (in script folder) works fine.

## Usage:
1. Clone the repository or download the script.
2. Navigate to the directory containing the script.
3. Run the script using Python:
    ```bash
    python <script_name>.py
    ```
4. The GUI will appear. Start by discovering cameras or manually adding them.
5. Configure your desired settings and start capturing!
6. To convert previously stored snapshots, simply select the relevant folder and the script will handle the rest.

## License
[![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

**Unifi Camera Timelapse Creator** © 2023 by Morris Lazootin is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).
