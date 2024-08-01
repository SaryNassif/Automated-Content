# Automated-Content by Sary Nassif

This script automates the creation of reddit posts as videos. It fetches screenshots of the posts, and combines it into an mp4 file with text to speech audio.

## Features

-Fetches Post from specified subreddit by the user using reddit API
-Converts post into a mp4 file using Google Text To Speech (gTTS)
-Takes a screenshot of the post using sellenium
-Combines Audio, Video, and Screenshot into one video using moviepy

## Installation

1. Clone the repository
    ```bash
    git clone https://github.com/SaryNassif/Automated-Content.git cd Automated-Content
    ```

2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Ensure you have the necessary software installed:
    - [Google Chrome](https://www.google.com/chrome/)
    - [ChromeDriver](https://sites.google.com/chromium.org/driver/)

## Usage

1. Run the script:
    ```bash
    python Script.py
    ```

2. Fill in your Reddit API credentials and subreddit information in the GUI.
3. Click the "Generate Reddit Video" button.
   
