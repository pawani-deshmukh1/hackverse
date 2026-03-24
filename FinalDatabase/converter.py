import base64
import os

def get_base64():
    print("\n--- AudioAuth: BASE64 CONVERTER ---")
    # Tell the script where the file is
    path = input("Enter the full path (e.g., dataset/human/hindi_test.wav): ")
    
    if not os.path.exists(path):
        print(f"❌ Error: {path} not found!")
        return

    # Turn the sound into text
    with open(path, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
        
    # Save the text to a file so you can send it to your team
    output_name = path.replace("/", "_").replace(".wav", ".txt")
    with open(output_name, "w") as f:
        f.write(encoded_string)
    
    print(f"✅ SUCCESS!")
    print(f"Text file created: {output_name}")
    print("Copy the text inside this file and send it to your ML teammate.")

if __name__ == "__main__":
    get_base64()