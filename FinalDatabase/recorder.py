import sounddevice as sd
from scipy.io.wavfile import write
import os

# --- SETTINGS ---
# 16000 is the quality AI models like best.
FS = 16000  
# 7 seconds is long enough for the AI to "hear" the voice patterns.
DURATION = 7 

def record_audio():
    print("-" * 30)
    print("AUDIO AUTH - DATA COLLECTOR")
    print("-" * 30)
    
    # 1. Ask for details
    category = input("Is this 'human' or 'ai'? ").lower()
    lang = input("What language? (e.g., hindi, english, tamil): ").lower()
    
    # 2. Create the folder path automatically
    folder_path = f"dataset/{category}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    filename = f"{folder_path}/{lang}_test.wav"

    # 3. Start Recording
    print(f"\nGET READY... Recording to: {filename}")
    print("Starting in 3... 2... 1...")
    
    # This captures the sound from your Mac's mic
    recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1)
    
    print("\n🔴 RECORDING NOW... SPEAK! 🔴")
    sd.wait() # This makes the computer wait until 7 seconds are up
    
    # 4. Save the file
    write(filename, FS, recording)
    print(f"\n✅ DONE! File saved in: {filename}")
    print("-" * 30)

if __name__ == "__main__":
    while True:
        record_audio()
        choice = input("Record another one? (y/n): ")
        if choice.lower() != 'y':
            print("Goodbye! Go win that hackathon!")
            break