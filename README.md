# UniFi Camera Timelapse Creator

This script provides a GUI to create timelapses from UniFi Cameras. It discovers cameras on your local network, captures snapshots based on a specified frequency, and then *automagically* compiles them into a timelapse video once the capturing session is complete.

![image](https://github.com/inertiacreeping/Unifi-Timelapse/assets/98634109/ef83bf4f-4cd7-4921-8eb1-a83a66052de3)

## Features:
- Automatically detects your network, then discovers available UniFi Cameras on your network.
- Configure capture settings like snapshot frequency and output video frame rate.
- One-click start for immediate timelapse creation.
- Schedule recordings to automatically create a timelapse during specific intervals.
- View metrics from the previous session, such as elapsed time, total captures, and estimated video length.
- Convert previously stored snapshots into a timelapse video.

## Prerequisites:

> [!IMPORTANT]
> Before using the script, ensure that you've previously logged into each UniFi camera and enabled the **Anonymous Snapshots** feature. 
> This is crucial for the script to be able to capture snapshots, as this script relies on scraping a snapshot from each Camera from **IP ADDRESS**/snap.jpeg

1. Log into **Unifi Protect**, click on the **Settings Cog** in the left-hand menu, click on **System** then reveal your **Recovery Code**. Copy this code.
    
![image](https://github.com/inertiacreeping/Unifi-Timelapse/assets/98634109/0703b263-0ab4-46a8-ab21-43c1c72c6b32)

2. Go to the **IP address** of your camera, which can be found in your Camera list in Unifi Protect
   
![image](https://github.com/inertiacreeping/Unifi-Timelapse/assets/98634109/15704de7-a7cc-4da9-b374-5924bb3a552b)

3. Sign into the camera using "**ubnt**" (username) and your recovery key (password)

![image](https://github.com/inertiacreeping/Unifi-Timelapse/assets/98634109/23bb9f78-a7e5-4d82-b3f0-ba46a7052a16)

4. In the **Configure** tab, enable **Anonymous Snapshot**, then click **Save Changes**

![image](https://github.com/inertiacreeping/Unifi-Timelapse/assets/98634109/7b9cd643-aac4-4f23-bb01-ff3f141730c7)

5. Now, if you append /snap.jpeg to the IP address of your camera, you should see a static jpeg snapshot of what the camera sees.

### Required dependencies:

1. [Python 3](https://www.python.org/downloads/)
2. [Tkinter](https://docs.python.org/3/library/tkinter.html) - For the GUI.
3. [Requests](https://docs.python-requests.org/en/master/) - For making HTTP requests to the cameras.
4. [FFmpeg](https://ffmpeg.org/download.html) - For converting images to video. System-wide or local install (ie, ffmpeg.exe located in script folder) works fine - this script will check for both.

## Usage:

### Specifying IP Addresses or IP Range

Without any user interaction, this script will detect the IP range your machine is using, then scan that entire IP Range for any IP address which returns an image at **IP.ADDRESS**/snap.jpeg (indicating that a Unifi camera exists at this IP address).

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

### Usage

1. Run the script.
2. Select one or more discovered cameras by clicking the checkboxes next to their IP addresses.
3. Change the desired capture rate and output video frames per second (FPS)
   - an estimate for frames, storage size, and video output length will be calculated and displayed below.
5. Click on:
   - "**Start capturing**" to begin an immediate capture session, or;
   - "**Start schedule** for the capture session to begin and end at a specific time.
       - If you start a schedule *inside* the sheduled times, the capturing will begin immediately.
       - There mgiht be a slight delay to the start/end of a scheduled capture session, due to the way the scheduler works.
7. To convert previously captured snapshots into a video (perhaps with a different framerate), click on the "**Convert Existing Images**" button, select the relevant folder of captured snapshots, and the script will handle the rest.

> [!NOTE]
> Captures will be stored in /captures/IP ADDRESS/Date_time.
> Videos are created and stored in the same folder as the captures.

## License
[![Creative Commons License](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc-sa/4.0/)

**Unifi Camera Timelapse Creator** © 2023 by Morris Lazootin is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

## Acknowledgements

### FFmpeg
This software includes [FFmpeg](https://ffmpeg.org/) licensed under the [LGPLv2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html).

The source code of FFmpeg can be found [here](https://ffmpeg.org/download.html).

