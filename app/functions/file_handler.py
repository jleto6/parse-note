import os
from pdf2image import convert_from_path
from PIL import Image
import magic
import subprocess
import io
import wave
import fitz
import json

from vosk import Model
from vosk import KaldiRecognizer
from vosk import SetLogLevel
SetLogLevel(-1)

from config import NOTE_INPUTS_DIR, RAW_TEXT, TOPIC_OUTPUTS_DIR
from functions.ocr import do_ocr

if not os.path.exists(RAW_TEXT):
    with open(RAW_TEXT, "w") as f:
        pass  # Just creates the file, does nothing else

# Text Splitter
def split_text(filename, split_size):
    text = open(filename, 'r', encoding='utf-8').read()
    space_ctr = 0
    file_ctr = 0
    chunk = ""
    for char in text:
        chunk += char
        if char == " ":
            space_ctr += 1
        if space_ctr >= split_size:
            with open(f"{TOPIC_OUTPUTS_DIR}/chunk_{file_ctr}.txt", 'w', encoding='utf-8') as f:
                f.write(chunk)
            file_ctr += 1
            chunk = ''
            space_ctr = 0
    # Write the last chunk if anything is left
    if chunk:
        if file_ctr == 0:
            # No full chunks were made, so create first file
            with open(f"{TOPIC_OUTPUTS_DIR}/chunk_0.txt", 'w', encoding='utf-8') as f:
                f.write(chunk)
        else:
            with open(f"{TOPIC_OUTPUTS_DIR}/chunk_{file_ctr-1}.txt", 'a', encoding='utf-8') as f:
                    f.write(chunk)

# File deleter
def clear_output(folder_path):
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
    except:
        os.remove(folder_path)

# Uploaded Files
folder = NOTE_INPUTS_DIR
files = os.listdir(folder) # List of files in notes folder 
if ".DS_Store" in files:
        files.remove(".DS_Store")
if "test_notes" in files:
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
def handle_image(file, file_path):
    img = Image.open(file_path) # Open the current image 
    img = img.convert("RGBA") # Convert to RGBA
    do_ocr(img)    


# Handle PDFs
def handle_pdf(file, file_path):
    doc = fitz.open(file_path) # Open the PDF file
    # Open the txt output file in append 
    with open (RAW_TEXT, "a", encoding="utf-8") as file:
        # go through pages of PDF one by one
        for page in doc:
            text = page.get_text().strip() # text extraction
            # # If the page text is short try OCR
            if len(text) < 10:
                pix = page.get_pixmap()         # Render page as image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Convert to PIL Image
                do_ocr(img)
            # If extraction fine
            else:
                # append extracted text
                file.write(text + "\n\n")
                

# Handle Videos
def handle_video(file, file_path):
    model = Model("data/en_model")  # Load the model
    # Convert file to wav
    process = subprocess.run(
    ["ffmpeg", "-i", file_path, "-f", "wav", "-ac", "1", "-ar", "16000", "pipe:1"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
    )
    audio_bytes = process.stdout
    wf = wave.open(io.BytesIO(audio_bytes), "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    # Iterate Thru Chunks of Audio File
    text = ""  # Initialize an empty string for transcript
    while True:
        data = wf.readframes(4000)  # Read next chunk
        if len(data) == 0:
            break  # Stop when the audio ends
        if rec.AcceptWaveform(data):  # If Vosk processes a chunk
            result = json.loads(rec.Result())  # Convert JSON result
            text += result["text"] + " "  # Append text

    # Write the transcription to the txt file
    with open(RAW_TEXT, "a") as f:
        f.write(text)
    
    

    