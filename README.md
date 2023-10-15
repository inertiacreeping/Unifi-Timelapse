# UniFi Camera Timelapse Creator

This script provides a GUI to create timelapses from UniFi Cameras. It discovers cameras on your local network, captures snapshots based on a specified frequency, and then compiles them into a timelapse video.

## Features:
- Automatically discover UniFi Cameras on your network.
- Configure capture settings like snapshot frequency and video frame rate.
- One-click start for immediate timelapse creation.
- Schedule recordings to automatically create a timelapse during specific intervals.
- View metrics from the previous session, such as elapsed time, total captures, and estimated video length.
- Convert previously stored snapshots into a timelapse video.

## Prerequisites:

Before using the script, ensure that you've logged into each UniFi camera and enabled the **Anonymous Snapshots** feature. This is crucial for the script to be able to capture snapshots.

1. [Python 3](https://www.python.org/downloads/)
2. [Tkinter](https://docs.python.org/3/library/tkinter.html) - For the GUI.
3. [Requests](https://docs.python-requests.org/en/master/) - For making HTTP requests to the cameras.
4. [FFmpeg](https://ffmpeg.org/download.html) - For converting images to video. System-wide or local install (in script folder) works fine.

## Usage:

### Specifying IP Addresses or IP Range

To make the search process more efficient, you can provide the script with either specific IP addresses of the cameras or an IP range to search within.

#### 1. **Specifying IP Addresses**:
   
   - Create a file named `IP.txt` in the root directory of the script.
   - Within this file, list down the IP addresses of the cameras, one address per line. 
   
     ```txt
     192.168.1.5
     192.168.1.6
     192.168.1.7
     ```

#### 2. **Specifying IP Range**:
   
   - If you'd like the script to search within a specific IP range, create a file named `IP_range.txt` in the root directory of the script.
   - Enter the desired IP range in this file. 

     ```txt
     192.168.1.1/24
     ```

     This will instruct the script to search for cameras within the 192.168.1.1 to 192.168.1.255 range.

### Automatic Search

If neither `IP.txt` nor `IP_range.txt` files are present, the script will default to automatically searching for cameras. It will attempt to detect the local network's IP range and search within that range for any available cameras.

1. Clone the repository or download the script.
2. Navigate to the directory containing the script.
3. Run the script using Python:
    ```bash
    python UnifiCameraTimelapse.py
    ```
4. The GUI will appear. Start by discovering cameras or manually adding them.
5. Configure your desired settings and start capturing!
6. To convert previously stored snapshots, simply select the relevant folder and the script will handle the rest.

## License
[![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

**Unifi Camera Timelapse Creator** © 2023 by Morris Lazootin is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

## Acknowledgements

### FFmpeg
This software includes [FFmpeg](https://ffmpeg.org/) licensed under the [LGPLv2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html).

The source code of FFmpeg can be found [here](https://ffmpeg.org/download.html).

