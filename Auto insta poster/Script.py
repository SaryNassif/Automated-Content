import customtkinter
from tkinter import StringVar, messagebox
from threading import Thread
from selenium.common.exceptions import NoSuchElementException
import json
import os
import logging
from gtts import gTTS
import requests
from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, CompositeVideoClip
from moviepy.video.fx import resize
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to toggle theme
def theme():
    current_theme = customtkinter.get_appearance_mode()
    customtkinter.set_appearance_mode("Dark" if current_theme == "Light" else "Light")

# Function to save credentials to JSON
def save_credentials():
    try:
        credentials = {
            "client_id": client_id_var.get(),
            "secret_id": secret_id_var.get(),
            "reddit_username": reddit_username_var.get(),
            "reddit_password": reddit_password_var.get(),
            "subreddit": subreddit_var.get(),
            "post_type": post_type_var.get()
        }
        with open("credentials.json", "w") as f:
            json.dump(credentials, f)
        logging.info("Credentials saved successfully.")
    except Exception as e:
        logging.error(f"Error saving credentials: {e}")

# Function to load credentials from JSON
def load_credentials():
    try:
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as f:
                credentials = json.load(f)
                client_id_var.set(credentials.get("client_id", ""))
                secret_id_var.set(credentials.get("secret_id", ""))
                reddit_username_var.set(credentials.get("reddit_username", ""))
                reddit_password_var.set(credentials.get("reddit_password", ""))
                subreddit_var.set(credentials.get("subreddit", ""))
                post_type_var.set(credentials.get("post_type", "Hot"))
            logging.info("Credentials loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading credentials: {e}")

# Function to generate Reddit video
def generate_reddit_video():
    messagebox.showinfo("Video Progress", "Loading... Please Wait, Check terminal for progress")
    GenerateButton.configure(state="disabled")

    try:
        # Save credentials
        save_credentials()

        # Get user inputs
        CLIENT_ID = client_id_var.get()
        SECRET_ID = secret_id_var.get()
        REDDIT_USERNAME = reddit_username_var.get()
        REDDIT_PASSWORD = reddit_password_var.get()
        SUBREDDIT = subreddit_var.get()
        POST_TYPE = post_type_var.get().lower()  # Convert to lowercase to match API requirement

        # Reddit authentication
        auth = requests.auth.HTTPBasicAuth(CLIENT_ID, SECRET_ID)
        data = {'grant_type': 'password', 'username': REDDIT_USERNAME, 'password': REDDIT_PASSWORD}
        headers = {'User-Agent': 'MyAPI/0.0.1'}
        res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data=data, headers=headers)
        TOKEN = res.json().get('access_token')
        headers['Authorization'] = f'bearer {TOKEN}'

        # Fetch posts and filter for SFW content and word limit
        res = requests.get(f'https://oauth.reddit.com/r/{SUBREDDIT}/{POST_TYPE}', headers=headers, params={'limit': '100'})
        posts = res.json()['data']['children']
        sfw_posts = [
            post['data'] for post in posts
            if not post['data']['over_18'] and 80 < len((post['data']['title'] + " " + post['data']['selftext']).split()) < 250
        ]

        if not sfw_posts:
            logging.info("No SFW posts found with word count between 80 and 250.")
            messagebox.showinfo("Video Progress", "No suitable posts found.")
            GenerateButton.configure(state="enabled")
            return

        post = sfw_posts[0]

        # Text to speech
        text = post['title'] + post['selftext']
        language = 'en'
        recording = gTTS(text=text, lang=language, slow=False)
        output_file = f"outputs/output_{post['id']}.mp3"
        recording.save(output_file)
        logging.info("Audio generated successfully.")
        messagebox.showinfo("Video Progress", "Audio is retrieved, screenshot and video still left")

        # Screenshot getter
        driver = webdriver.Chrome()
        driver.get(f'https://www.reddit.com{post["permalink"]}')

        try:
            # Wait for the page to load and find the main content
            wait = WebDriverWait(driver, 10)
            post_content = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "shreddit-post")))

            # Take screenshot of the post content
            screenshot_file = f"outputs/screenshot_{post['id']}.png"
            post_content.screenshot(screenshot_file)
        except (NoSuchElementException, TimeoutException):
            logging.warning("Could not find or interact with the element for screenshot. Taking a screenshot of the whole page as fallback.")
            screenshot_file = f"outputs/screenshot_{post['id']}_fallback.png"
            driver.save_screenshot(screenshot_file)
        finally:
            driver.quit()
            logging.info("Screenshot taken successfully.")
            messagebox.showinfo("Video Progress", "Audio and screenshot are complete, combining both shortly.")

        # Combining audio + video + screenshot
        audio_duration = AudioFileClip(output_file).duration
        video_clip = VideoFileClip("BackgroundVid.mp4").subclip(0, audio_duration)
        video_clip = video_clip.set_audio(AudioFileClip(output_file))
        screenshot = ImageClip(screenshot_file)
        video_width, video_height = video_clip.size
        screenshot_width, screenshot_height = screenshot.size
        x_pos = (video_width - screenshot_width) // 2
        y_pos = (video_height - screenshot_height) // 2
        screenshot = screenshot.set_position((x_pos, y_pos))

        if screenshot_width > video_width or screenshot_height > video_height:
            screenshot = resize(screenshot, width=video_width, height=video_height)

        screenshot = screenshot.set_duration(audio_duration)
        Combination = CompositeVideoClip([video_clip, screenshot])
        Combination = Combination.set_duration(audio_duration)
        Combination.write_videofile(f"outputs/Video{post['id']}.mp4", codec='libx264')

        logging.info("Video generated successfully.")
        messagebox.showinfo("Video Progress", "Video is complete, check the output folder")
    except Exception as e:
        logging.error(f"Error generating video: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        GenerateButton.configure(state="enabled")

# Function to start a new thread for video generation
def start_generate_reddit_video_thread():
    thread = Thread(target=generate_reddit_video)
    thread.start()

# tkinter setup
customtkinter.set_default_color_theme("blue")
customtkinter.set_appearance_mode("dark")

root = customtkinter.CTk()
root.title("Automation - Sary Nassif")
root.geometry("400x650")
root.minsize(400,650)

label = customtkinter.CTkLabel(master=root, text="Automated Content - Sary Nassif")
label.pack(padx=1, pady=1)

frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=20, padx=60, fill="both", expand=True)

client_id_var = StringVar()
secret_id_var = StringVar()
reddit_username_var = StringVar()
reddit_password_var = StringVar()
subreddit_var = StringVar()
post_type_var = StringVar()

client_id_label = customtkinter.CTkLabel(master=frame, text="Client ID")
client_id_label.pack(pady=(10, 0))
client_id_entry = customtkinter.CTkEntry(master=frame, textvariable=client_id_var)
client_id_entry.pack(pady=(0, 10))

secret_id_label = customtkinter.CTkLabel(master=frame, text="Secret ID")
secret_id_label.pack(pady=(10, 0))
secret_id_entry = customtkinter.CTkEntry(master=frame, textvariable=secret_id_var)
secret_id_entry.pack(pady=(0, 10))

reddit_username_label = customtkinter.CTkLabel(master=frame, text="Reddit Username")
reddit_username_label.pack(pady=(10, 0))
reddit_username_entry = customtkinter.CTkEntry(master=frame, textvariable=reddit_username_var)
reddit_username_entry.pack(pady=(0, 10))

reddit_password_label = customtkinter.CTkLabel(master=frame, text="Reddit Password")
reddit_password_label.pack(pady=(10, 0))
reddit_password_entry = customtkinter.CTkEntry(master=frame, textvariable=reddit_password_var)
reddit_password_entry.pack(pady=(0, 10))

subreddit_label = customtkinter.CTkLabel(master=frame, text="Subreddit Name (not link)")
subreddit_label.pack(pady=(10, 0))
subreddit_entry = customtkinter.CTkEntry(master=frame, textvariable=subreddit_var)
subreddit_entry.pack(pady=(0, 10))

post_type_label = customtkinter.CTkLabel(master=frame, text="Post Type")
post_type_label.pack(pady=(10, 0))
post_type_options = ["Hot", "New", "Top"]
post_type_menu = customtkinter.CTkOptionMenu(master=frame, variable=post_type_var, values=post_type_options)
post_type_menu.pack(pady=(0, 10))

GenerateButton = customtkinter.CTkButton(master=frame, text="Generate Reddit Video", command=start_generate_reddit_video_thread)
GenerateButton.pack(pady=10)

themeButton = customtkinter.CTkButton(master=root, text="💡", command=theme)
themeButton.pack(pady=10)

# Load credentials on startup
load_credentials()

root.mainloop()