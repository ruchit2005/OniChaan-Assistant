import speech_recognition as sr
import os
import time
import subprocess
import threading
from threading import Thread
import webbrowser
import requests
import json
import urllib.parse
import base64
import asyncio
from gemini_handler import GeminiHandler

from dotenv import load_dotenv
load_dotenv()


import tkinter as tk
from new_ui import AnimeWaifuApp  # Import the UI class

class SpotifyVoiceBot:
    def __init__(self, ui_app=None):
        self.ui_app = ui_app
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = True

        # Gemini setup
        self.gemini = GeminiHandler(api_key=os.getenv("GEMINI_API_KEY"))

        # Spotify credentials
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.access_token = None

        self.get_access_token()

        print("Adjusting for ambient noise... Please wait.")
        if self.ui_app:
            self.ui_app.update_status("Adjusting for ambient noise...")

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

        print("Ready to listen!")
        if self.ui_app:
            self.ui_app.update_status("Ready to listen!")


    def get_access_token(self):
        """Get Spotify access token using Client Credentials flow"""
        try:
            token_url = "https://accounts.spotify.com/api/token"
            client_credentials = f"{self.client_id}:{self.client_secret}"
            client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {client_credentials_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print("Successfully obtained Spotify access token!")
                return True
            else:
                print(f"Failed to get access token: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error getting access token: {e}")
            return False

    def search_spotify_track(self, song_name):
        """Search for a song on Spotify and return the first result's track ID"""
        if not self.access_token:
            return None
            
        try:
            search_url = "https://api.spotify.com/v1/search"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"q": song_name, "type": "track", "limit": 1}
            
            response = requests.get(search_url, headers=headers, params=params)
            
            if response.status_code == 200:
                search_data = response.json()
                tracks = search_data.get("tracks", {}).get("items", [])
                
                if tracks:
                    track = tracks[0]
                    track_id = track["id"]
                    track_name = track["name"]
                    artist_name = track["artists"][0]["name"]
                    print(f"Found: {track_name} by {artist_name}")
                    return track_id, track_name, artist_name
                else:
                    print(f"No tracks found for: {song_name}")
                    return None
            else:
                print(f"Search failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error searching for track: {e}")
            return None

    def listen_for_commands(self):
        while self.listening:
            try:
                with self.microphone as source:
                    print("Listening for command...")
                    if self.ui_app:
                        self.ui_app.update_status("Listening...")
                    
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)

                try:
                    command = self.recognizer.recognize_google(audio).lower()
                    print(f"You said: {command}")

                    if command.startswith("play "):
                        song_name = command[5:]
                        print(f"Command recognized! Searching for: {song_name}")
                        if self.ui_app:
                            self.ui_app.update_status(f"Searching for: {song_name}")
                        self.play_song_on_spotify(song_name)

                    elif "play" in command and len(command.split()) >= 2:
                        words = command.split()
                        try:
                            play_index = words.index("play")
                            if play_index + 1 < len(words):
                                song_name = " ".join(words[play_index + 1:])
                                print(f"Command recognized! Searching for: {song_name}")
                                if self.ui_app:
                                    self.ui_app.update_status(f"Searching for: {song_name}")
                                self.play_song_on_spotify(song_name)
                        except ValueError:
                            pass

                    else:
                        # Gemini fallback
                        prompt = (
                            f"You are Oniichan's helpful anime waifu assistant. "
                            f"Respond in a cute and kind way to this message from Oniichan:\n"
                            f"{command}"
                        )
                        response = self.gemini.chat(prompt)
                        print(f"Gemini: {response}")
                        if self.ui_app:
                            self.ui_app.update_status(response)
                            asyncio.run(self.ui_app.speak(response))


                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")

            except sr.WaitTimeoutError:
                pass
            except KeyboardInterrupt:
                print("\nStopping voice bot...")
                self.listening = False
                break
            except FileNotFoundError as e:
                print(f"Speech error: missing command: {e.filename}")


    def play_song_on_spotify(self, song_name):
        """Search for the song and play it on Spotify"""
        try:
            song_name = song_name.strip()
            print(f"Searching for '{song_name}' on Spotify...")
            
            result = self.search_spotify_track(song_name)
            
            if result:
                track_id, track_name, artist_name = result
                print(f"Found track ID: {track_id}")
                
                # Make the waifu speak first, then play the song after speaking is done
                if self.ui_app:
                    # Create a callback function to play the song after speaking
                    def play_after_speaking():
                        self.open_spotify_with_track(f"{track_name} by {artist_name}", track_id)
                    
                    # Waifu speaks first, then plays the song
                    self.ui_app.speak_song_playing(f"{track_name} by {artist_name}", callback=play_after_speaking)
                else:
                    # If no UI, play directly
                    self.open_spotify_with_track(f"{track_name} by {artist_name}", track_id)
            else:
                print("Track not found via API, falling back to web search...")
                self.fallback_web_spotify(song_name, None)
                
        except Exception as e:
            print(f"Error playing song: {e}")
            self.fallback_web_spotify(song_name, None)

    def open_spotify_with_track(self, song_name, track_id):
        """Open Spotify and play the specific track"""
        try:
            if os.name == 'nt':  # Windows
                try:
                    subprocess.Popen(['spotify'])
                    time.sleep(4)
                    
                    track_uri = f"spotify:track:{track_id}"
                    subprocess.Popen(['start', track_uri], shell=True)
                    print(f"Now playing: {song_name}")
                    
                except Exception as e:
                    print(f"Could not open Spotify app: {e}")
                    self.fallback_web_spotify(song_name, track_id)
                    
            elif os.name == 'posix':  # macOS/Linux
                try:
                    import platform
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.Popen(['open', '-a', 'Spotify'])
                        time.sleep(4)
                        
                        track_uri = f"spotify:track:{track_id}"
                        os.system(f'open "{track_uri}"')
                        print(f"Now playing: {song_name}")
                    else:
                        subprocess.Popen(['spotify'])
                        time.sleep(4)
                        
                        track_uri = f"spotify:track:{track_id}"
                        os.system(f'xdg-open "{track_uri}"')
                        print(f"Now playing: {song_name}")
                        
                except Exception as e:
                    print(f"Could not open Spotify app: {e}")
                    self.fallback_web_spotify(song_name, track_id)
            
        except Exception as e:
            print(f"Error opening Spotify: {e}")
            self.fallback_web_spotify(song_name, track_id)

    def fallback_web_spotify(self, song_name, track_id=None):
        """Fallback method: Open Spotify Web Player"""
        try:
            print("Opening Spotify Web Player...")
            
            if track_id:
                direct_url = f"https://open.spotify.com/track/{track_id}"
                webbrowser.open(direct_url)
                print(f"Opened direct link for: {song_name}")
                print("The song should start playing automatically in the web player!")
            else:
                formatted_song = song_name.replace(' ', '%20')
                search_web_url = f"https://open.spotify.com/search/{formatted_song}"
                webbrowser.open(search_web_url)
                print(f"Opened web search for: {song_name}")
                print("Click on the first search result to play!")
                
        except Exception as e:
            print(f"Could not open Spotify Web Player: {e}")

    def stop_listening(self):
        """Stop the voice bot"""
        self.listening = False

def run_bot_with_ui():
    """Run the bot with UI in a separate thread"""
    def bot_thread():
        # Create and start the voice bot with UI reference
        bot = SpotifyVoiceBot(ui_app=app)
        
        if not bot.access_token:
            print("WARNING: No Spotify API access. The bot will work but with limited functionality.")
            if app:
                app.update_status("WARNING: Limited Spotify API access")
        
        try:
            # Start listening
            bot.listen_for_commands()
                
        except KeyboardInterrupt:
            print("\nShutting down voice bot...")
            bot.stop_listening()

    # Create the UI
    root = tk.Tk()
    app = AnimeWaifuApp(root)
    
    # Start the bot in a separate thread
    bot_thread_obj = Thread(target=bot_thread)
    bot_thread_obj.daemon = True
    bot_thread_obj.start()
    
    # Handle window closing
    def on_closing():
        print("Shutting down...")
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the UI main loop
    root.mainloop()

def main():
    print("=== Waifu Spotify Voice Bot ===")
    print("Starting with anime waifu UI...")
    print()
    print("Requirements:")
    print("1. Make sure 'sparkle-erio.gif' is in the same folder")
    print("2. Install required packages: pip install edge-tts pydub pillow")
    print("3. Make sure you have a microphone connected")
    print("4. Spotify should be installed (desktop app preferred)")
    print()
     
    run_bot_with_ui()

if __name__ == "__main__":
    main()