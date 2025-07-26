import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import edge_tts
import asyncio
import threading
import playsound
from pydub import AudioSegment
from pydub.playback import play
import io

class AnimeWaifuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Waifu AI")
        self.root.geometry("700x600")  # Adjust as per your gif size
        self.root.configure(bg="black")

        # Load the animated GIF
        self.img = Image.open("sparkle-erio.gif")  # Replace with your gif file
        self.frames = [ImageTk.PhotoImage(frame.copy().resize((700, 600), Image.Resampling.LANCZOS).convert("RGBA"))
                       for frame in ImageSequence.Iterator(self.img)]

        self.label = tk.Label(self.root, bg="black")
        self.label.pack(pady=20)

        self.frame_index = 0
        self.animate()

        self.root.after(1000, self.speak_async)


    def animate(self):
        frame = self.frames[self.frame_index]
        self.label.configure(image=frame)
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.root.after(100, self.animate)  # Adjust speed if needed

    def speak_async(self):
        threading.Thread(target=self.run_speak).start()

    def run_speak(self):
        asyncio.run(self.speak("""
Good morning, my dear! I hope you slept well. I made sure to keep things quiet while you were resting... hehe~                               
"""))

    async def speak(self, text):
        communicate = edge_tts.Communicate(
            text=text,
            voice="ja-JP-NanamiNeural"  # Anime-style Japanese voice
        )

        stream = communicate.stream()

        auido_data = bytearray()
        
        async for chunk in stream:
            if chunk["type"] == "audio":
                auido_data.extend(chunk["data"])

        sound = AudioSegment.from_file(io.BytesIO(auido_data), format="mp3")
        play(sound)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimeWaifuApp(root)
    root.mainloop()
