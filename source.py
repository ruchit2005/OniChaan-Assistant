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

# ────────────────────────────────────────
# 🔐 Gemini API Setup
genai.configure(api_key="AIzaSyBQX9f76wKPbBByq42AFu8iwGxB4QoVgwQ")
llm_model = genai.GenerativeModel("gemini-1.5-flash")

print(genai.list_models())  # Shows all available model names

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

model = Model('vosk-model-en-us-0.22-lgraph')  # 🔁 Path to your downloaded model
recognizer = KaldiRecognizer(model, sample_rate)
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

# ────────────────────────────────────────
# 💻 OS Command Execution Handler
def try_os_command(text):
    lowered = text.lower()

    if "open spotify" in lowered:
        try:
            subprocess.Popen(["C:\\Users\\Mitul Gupta\\AppData\\Roaming\\Spotify\\Spotify.exe"])
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

    elif "shutdown" in lowered:
        return "Ehh?! Oniichan don't make me shut down~ 😭"

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
# 🎬 Main Loop
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
    