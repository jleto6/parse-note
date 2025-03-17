import os
from pdf2image import convert_from_path
from PIL import Image
import magic
import subprocess

import wave
import logging
import sys
import json
from vosk import Model
from vosk import KaldiRecognizer
from vosk import SetLogLevel
SetLogLevel(-1)

model = Model("en_model")  # Load the model

# Uploaded Files
folder = "notes"
files = os.listdir(folder) # List of files in notes folder 
if ".DS_Store" in files:
        files.remove(".DS_Store")
if "test_notes" in files:
        print("hi")
        files.remove("test_notes")

# Get The File Type
def get_file_type(file):
    file_path = os.path.join(folder, file)  # Get full file path
    file_type = magic.from_file(file_path, mime=True) # Detects file type
    file_type = file_type.split("/")[-1]
    file_type = file_type.upper()
    print(f"{file_path} | {file_type}")
    
    return file_path, file_type

# Handle Images
pngs_folder = "conversions/converted_pngs" # Folder of converted pngs
os.makedirs(pngs_folder, exist_ok=True) # Make folder if it doesnt exist

def handle_image(file, file_path):

    img = Image.open(file_path) # Open the current image 
    img = img.convert("RGBA") # Convert to RGBA

    base_name = os.path.splitext(file)[0] + ".png"  # Create the output filename with a .png extention
    output_file = os.path.join(pngs_folder, base_name) # Create full file path by joining 'pngs folder' and the file name
    img.save(output_file, "PNG")
    #print(f"Output file:{output_file}"

# Handle PDFs
def handle_pdf(file, file_path):

    images = convert_from_path(file_path) # Convert PDF pages to a list of images
    # Save each page as a PNG in the output folder
    for i, image in enumerate(images):
        image.save(os.path.join(pngs_folder, f"page_{i+1}.png"), "PNG")

# Handle Videos
wavs_folder = "conversions/converted_wavs" # Folder of converted wavs
txt_folder = "output_texts"

os.makedirs(wavs_folder, exist_ok=True) # Make folder if it doesnt exist

def handle_video(file, file_path):
    # Convert Video to WAV
    base_name = os.path.splitext(file)[0] + ".wav" # Create the output filename with a .wav extension
    output_file = os.path.join(wavs_folder, base_name) # Create full file path by joining 'wavs folder' and file name
    subprocess.run(["ffmpeg", "-i", file_path, "-ac", "1", "-ar", "16000", output_file, "-y"], # Convert video file to audio file and save it
               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) # Supress output other than errors
    
    # Convert WAV to text
    wf = wave.open(output_file, "rb")  # Open the WAV file in read-binary mode
    rec = KaldiRecognizer(model, wf.getframerate())  # Create recognizer

    # Iterate Thru Chunks of Audio File
    text = ""  # Initialize an empty string for transcript
    while True:
        data = wf.readframes(4000)  # Read next chunk
        if len(data) == 0:
            break  # Stop when the audio ends
        if rec.AcceptWaveform(data):  # If Vosk processes a chunk
            result = json.loads(rec.Result())  # Convert JSON result
            text += result["text"] + " "  # Append text

    # Create a text file
    counter = 1
    filename = f"output{counter}.txt"
    while os.path.exists(os.path.join(txt_folder, filename)):   # Keep incrementing if the filename already exists in txt_folder
        counter +=1
        filename = f"output{counter}.txt"
    txt_path = os.path.join(txt_folder, filename)  # Create full file path inside the folder

    # Write the transcription to the txt file
    with open(txt_path, "w") as f:
        f.write(text)
    
#for file in files:
 #   file_path, file_type = get_file_type(file)
  #  handle_video(file, file_path)

    

    