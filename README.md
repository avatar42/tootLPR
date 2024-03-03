# tootLPR
Simple script to be called from Blue Iris which marks up image with detections and toots the result along with found plates

## Set up software
[Install Cygwin](https://www.cygwin.com/)
It might not be technically needed but Blue Iris seemed to have issues running python directly.

[Install Python. I used 3.10](https://www.python.org/downloads/)

### Run the following from a command window:

python.exe -m pip install --upgrade pip

pip install Image

pip install datetime

pip install requests

pip install toot

toot login --instance [host name]

**Note be sure to login as the user that will be running the script. In the case of Blue Iris this is generally the Administrator account.**

## Configure
Edit the paths in [toolLPR.sh](https://github.com/avatar42/tootLPR/blob/main/tootLPR.sh) and [tootLPRtest.bat](https://github.com/avatar42/tootLPR/blob/main/tootLPRtest.bat)

Edit the URLs to the AI servers in [cfg.py](https://github.com/avatar42/tootLPR/blob/main/cfg.py)

## Test setup

Run [tootLPRtest.bat](https://github.com/avatar42/tootLPR/blob/main/tootLPRtest.bat)

## Set up Blue Iris
![Screenshot](https://raw.githubusercontent.com/avatar42/tootLPR/main/Screenshot%202024-03-02%20212539.png)

On the camera's **Alert** tab click on **On Alert**

On the **Alert Set** dialog create a set to **Run a script**

### Fill these fields

**Required AI Objects** Will call the script if any of theses objects are detected.

**File** Full path the the sh command

**Parameters** full path to [toolLPR.sh](https://github.com/avatar42/tootLPR/blob/main/tootLPR.sh) followed with **&ALERT_PATH**

**&ALERT_PATH** is replaced with the image file name by Blue Iris
