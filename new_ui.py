import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import edge_tts
import asyncio
import threading
from pydub import AudioSegment
from pydub.playback import play
import io

class AnimeWaifuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Waifu AI - Spotify Voice Bot")
        self.root.geometry("700x600")
        self.root.configure(bg="black")

        # Load the animated GIF
        try:
            self.img = Image.open("sparkle-erio.gif")  # Replace with your gif file
            self.frames = [ImageTk.PhotoImage(frame.copy().resize((700, 600), Image.Resampling.LANCZOS).convert("RGBA"))
                           for frame in ImageSequence.Iterator(self.img)]
        except FileNotFoundError:
            print("Warning: sparkle-erio.gif not found. Using placeholder.")
            # Create a simple placeholder if GIF is not found
            placeholder = Image.new('RGBA', (700, 600), (50, 50, 50, 255))
            self.frames = [ImageTk.PhotoImage(placeholder)]

        self.label = tk.Label(self.root, bg="black")
        self.label.pack(pady=20)

        # Status label
        self.status_label = tk.Label(self.root, text="Initializing...", 
                                   fg="white", bg="black", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.frame_index = 0
        self.animate()

        # Initial greeting
        self.root.after(1000, self.initial_greeting)

    def animate(self):
        frame = self.frames[self.frame_index]
        self.label.configure(image=frame)
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.root.after(100, self.animate)

    def initial_greeting(self):
        self.update_status("Ready to listen!")
        threading.Thread(target=self.run_initial_speak).start()

    def run_initial_speak(self):
        asyncio.run(self.speak("""
"""))

    def speak_song_playing(self, song_name, callback=None):
        """Public method to make the waifu speak about playing a song"""
        message = f"Playing {song_name} for you, my dear!"
        self.update_status(f"Playing: {song_name}")
        
        def speak_and_callback():
            asyncio.run(self.speak(message))
            if callback:
                callback()  # Call the callback after speaking is done
        
        threading.Thread(target=speak_and_callback).start()

    def update_status(self, status):
        """Update the status label"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status)

    async def speak(self, text):
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice="ja-JP-NanamiNeural"  # Anime-style Japanese voice
            )

            stream = communicate.stream()
            audio_data = bytearray()
            
            async for chunk in stream:
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

            sound = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            play(sound)
        except Exception as e:
            print(f"Speech error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimeWaifuApp(root)
    root.mainloop()