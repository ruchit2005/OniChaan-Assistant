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

class SpotifyVoiceBot:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = True
        
        # Spotify API credentials (you'll need to set these up)
        self.client_id = "4c4b888058944d2d898ed0e31d21def4"  # Replace with your Spotify app client ID
        self.client_secret = "3606e5ebe8e749e78d758af4c7437b2b"  # Replace with your Spotify app client secret
        self.access_token = None
        
        # Get access token on initialization
        self.get_access_token()
        
        # Adjust for ambient noise
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready to listen!")

    def get_access_token(self):
        """Get Spotify access token using Client Credentials flow"""
        try:
            # Spotify token endpoint
            token_url = "https://accounts.spotify.com/api/token"
            
            # Create the authorization header
            client_credentials = f"{self.client_id}:{self.client_secret}"
            client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()
            
            # Request headers
            headers = {
                "Authorization": f"Basic {client_credentials_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Request body
            data = {
                "grant_type": "client_credentials"
            }
            
            # Make the request
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                print("Successfully obtained Spotify access token!")
                return True
            else:
                print(f"Failed to get access token: {response.status_code}")
                print("Falling back to web search method...")
                return False
                
        except Exception as e:
            print(f"Error getting access token: {e}")
            print("Falling back to web search method...")
            return False

    def search_spotify_track(self, song_name):
        """Search for a song on Spotify and return the first result's track ID"""
        if not self.access_token:
            return None
            
        try:
            # Spotify search endpoint
            search_url = "https://api.spotify.com/v1/search"
            
            # Request headers
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            # Request parameters
            params = {
                "q": song_name,
                "type": "track",
                "limit": 1
            }
            
            # Make the search request
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
                    return track_id
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
        """Continuously listen for voice commands"""
        while self.listening:
            try:
                with self.microphone as source:
                    print("Listening for 'Play [song name]'...")
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                try:
                    # Recognize speech using Google's speech recognition
                    command = self.recognizer.recognize_google(audio).lower()
                    print(f"You said: {command}")
                    
                    # Check if command starts with "play"
                    if command.startswith("play "):
                        song_name = command[5:]  # Remove "play " from the beginning
                        print(f"Command recognized! Searching for: {song_name}")
                        self.play_song_on_spotify(song_name)
                    elif "play" in command and len(command.split()) >= 2:
                        # Handle cases like "can you play perfect" or "please play perfect"
                        words = command.split()
                        try:
                            play_index = words.index("play")
                            if play_index + 1 < len(words):
                                song_name = " ".join(words[play_index + 1:])
                                print(f"Command recognized! Searching for: {song_name}")
                                self.play_song_on_spotify(song_name)
                        except ValueError:
                            pass
                    
                except sr.UnknownValueError:
                    # Speech was not clear enough
                    pass
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                    
            except sr.WaitTimeoutError:
                # No speech detected within timeout
                pass
            except KeyboardInterrupt:
                print("\nStopping voice bot...")
                self.listening = False
                break

    def play_song_on_spotify(self, song_name):
        """Search for the song and play it on Spotify"""
        try:
            # Clean up the song name
            song_name = song_name.strip()
            
            # Search for the track ID dynamically
            print(f"Searching for '{song_name}' on Spotify...")
            track_id = self.search_spotify_track(song_name)
            
            if track_id:
                print(f"Found track ID: {track_id}")
                self.open_spotify_with_track(song_name, track_id)
            else:
                print("Track not found via API, falling back to web search...")
                self.fallback_web_spotify(song_name, None)
                
        except Exception as e:
            print(f"Error playing song: {e}")
            self.fallback_web_spotify(song_name, None)

    def open_spotify_with_track(self, song_name, track_id):
        """Open Spotify and play the specific track"""
        try:
            # Method 1: Try to open Spotify desktop app directly
            if os.name == 'nt':  # Windows
                try:
                    # Try to start Spotify app
                    subprocess.Popen(['spotify'])
                    time.sleep(4)  # Wait for Spotify to load
                    
                    # Use direct track URI for automatic playback
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
                        # For Linux
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
                # Direct link to the specific track
                direct_url = f"https://open.spotify.com/track/{track_id}"
                webbrowser.open(direct_url)
                print(f"Opened direct link for: {song_name}")
                print("The song should start playing automatically in the web player!")
            else:
                # Search link as fallback
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

def main():
    print("=== Spotify Voice Bot Setup ===")
    print("IMPORTANT: You need to set up Spotify API credentials first!")
    print("1. Go to https://developer.spotify.com/dashboard")
    print("2. Create a new app")
    print("3. Copy your Client ID and Client Secret")
    print("4. Replace 'YOUR_CLIENT_ID' and 'YOUR_CLIENT_SECRET' in the code")
    print("5. Run the script again")
    print()
    
    # Create and start the voice bot
    bot = SpotifyVoiceBot()
    
    if not bot.access_token:
        print("WARNING: No Spotify API access. The bot will work but with limited functionality.")
        print("It will fall back to opening web search results.")
        print()
    
    try:
        # Start listening in a separate thread
        listen_thread = Thread(target=bot.listen_for_commands)
        listen_thread.daemon = True
        listen_thread.start()
        
        print("Voice bot is running. Say 'Play [song name]' to search and play any song.")
        print("Examples: 'Play Perfect', 'Play Bohemian Rhapsody', 'Play Shape of You'")
        print("Press Ctrl+C to stop the bot.")
        
        # Keep the main thread alive
        while bot.listening:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down voice bot...")
        bot.stop_listening()

if __name__ == "__main__":
    main()