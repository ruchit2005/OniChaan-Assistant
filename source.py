import vosk
import pyttsx3
import sounddevice as sd
import queue
import sys
import json
import google.generativeai as genai
import atexit
import subprocess
import webbrowser
from vosk import Model, KaldiRecognizer
from spotipy.oauth2 import SpotifyOAuth
import spotipy

# ────────────────────────────────────────
# 🔐 Gemini API Setup
genai.configure(api_key="AIzaSyBQX9f76wKPbBByq42AFu8iwGxB4QoVgwQ")
llm_model = genai.GenerativeModel("gemini-1.5-flash")

# ────────────────────────────────────────
# 🗣️ TTS Waifu Voice Setup
engine = pyttsx3.init()
engine.setProperty('rate', 170)
voices = engine.getProperty('voices')
if len(voices) > 1:
    engine.setProperty('voice', voices[1].id)  # Usually female voice

@atexit.register
def cleanup():
    engine.stop()
    print("🧹 Cleaned up safely.")

# ────────────────────────────────────────
# 🎤 Vosk Speech-to-Text Setup
print(sd.query_devices())  # View your mic index
device_index = 3           # 🔁 Replace with your actual mic index

info = sd.query_devices(device_index, 'input')
sample_rate = int(info['default_samplerate'])
print("Mic sample rate:", sample_rate)

model = Model('vosk-model-en-us-0.22-lgraph')
recognizer = KaldiRecognizer(model, sample_rate)
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# ────────────────────────────────────────
# 🎵 Spotify Setup
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="a8ab1d4630bb40da869b3523bb189e3b",
    client_secret="fe245ae172ad4b11ae11b24dda25f00fT",
    redirect_uri="http://localhost:8888/callback",
    scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
))

def control_spotify(text):
    lowered = text.lower()

    try:
        if "pause spotify" in lowered or "pause music" in lowered:
            sp.pause_playback()
            return "Paused the music, Oniichan~ 🎶"

        elif "play music" in lowered or "resume spotify" in lowered:
            sp.start_playback()
            return "Resuming your music, enjoy~ 🎷"

        elif "next song" in lowered or "skip" in lowered:
            sp.next_track()
            return "Skipping ahead~ ⏭️"

        elif "previous song" in lowered:
            sp.previous_track()
            return "Going back, just like our memories~ ⏮️"

        elif "play" in lowered:
            query = lowered.replace("play", "").strip()
            result = sp.search(q=query, type="track", limit=1)
            if result["tracks"]["items"]:
                uri = result["tracks"]["items"][0]["uri"]
                sp.start_playback(uris=[uri])
                return f"Playing {query} just for you, Oniichan~ 💕"
            else:
                return "Hmm I can't find that song gomen~ 😿"

    except Exception as e:
        print(f"Spotify Error: {e}")
        return "Spotify-chan is being tsundere... can't control her now."

    return None

# ────────────────────────────────────────
# 💻 OS Command Execution Handler
def try_os_command(text):
    spotify_response = control_spotify(text)
    if spotify_response:
        return spotify_response

    lowered = text.lower()

    if "open spotify" in lowered:
        try:
            subprocess.Popen("start spotify", shell=True)
            return "Hai hai~ Opening Spotify for you Oniichan~ 🎵"
        except Exception:
            return "Gomen~ I couldn't open Spotify..."

    elif "open browser" in lowered or "open google" in lowered:
        webbrowser.open("https://www.google.com")
        return "Opening your browser Oniichan~ 🌐"

    elif "open youtube" in lowered:
        webbrowser.open("https://youtube.com")
        return "Here's YouTube Oniichan~ Enjoy your anime clips!"

    elif "open camera" in lowered:
        try:
            subprocess.Popen("start microsoft.windows.camera:", shell=True)
            return "Say cheese Oniichan~ Opening your camera 📸"
        except Exception:
            return "I tried, but your camera won't open, gomenasai..."

    return None

# ────────────────────────────────────────
# 🧠 Ask Gemini LLM
def ask_llm(prompt):
    try:
        print(f"\n🧠 Sending to Waifu LLM: {prompt}")
        response = llm_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "Gomenasai Oniichan~ I can't respond right now..."

# ────────────────────────────────────────
# 🎮 Main Loop
with sd.RawInputStream(samplerate=sample_rate, blocksize=8000, dtype='int16',
                       channels=1, callback=callback, device=device_index):
    print("🎤 Waifu is listening... Speak now Oniichan~ (Ctrl+C to stop)")
    try:
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    print(f"\n🗣️ You said: {text}")
                    command_response = try_os_command(text)

                    if command_response:
                        print(f"💻 OS Waifu: {command_response}")
                        engine.say(command_response)
                        engine.runAndWait()
                    else:
                        response = ask_llm(f"You're a cute anime waifu. Respond lovingly to Oniichan who said: '{text}'")
                        print(f"💬 Waifu: {response}")
                        engine.say(response)
                        engine.runAndWait()
            else:
                partial = json.loads(recognizer.PartialResult())
                print("Listening:", partial.get("partial", ""), end="\r")

    except KeyboardInterrupt:
        print("\n🛑 Oniichan, you stopped me~")
