import os
import time
import pandas as pd
import glob
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

from functions.ocr import do_ocr
from functions.gpt_call import image_call, text_call
from functions.conversions import handle_image, handle_pdf, get_file_type, handle_video

from app import app
from threading import Thread
import threading

def run_flask():
    app.run(debug=True, use_reloader=False)  # Starts Flask but doesn't block main.py

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Start the file watcher in a background thread
print("Flask is running, but main.py can still execute other code.")

# PDF maker
def create_pdf(filename, text):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    # Split text into paragraphs (preserving newlines)
    for paragraph in text.split("\n\n"):  # Splits at paragraphs (double newlines for paragraphs)
        story.append(Paragraph(paragraph.replace("\n", "<br/>"), styles["Normal"]))
    # Create the pdf
    doc.build(story)

# File deleter
def clear_output(folder_path):
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
# -----------------------------------------------
#  Main
# -----------------------------------------------

def main():

    # Clear previous outputs on run
    clear_output("conversions")
    clear_output("output_texts")
    clear_output("static/files")

    output_text = "notes.txt"   # Text file of all GPT note outputs
    open("notes.txt", "w").close()  # Ensure the file exists by creating it if it doesnt

    # Uploaded Files
    folder = "notes"
    files = os.listdir(folder) # List of files in notes folder 

    if ".DS_Store" in files:
        files.remove(".DS_Store")

    if not files:
        print("No available files in the folder.")
        while not files:
            #print("Waiting for files.")
            files = os.listdir(folder) # List of files in notes folder 
    else:
        print("Files found:", files)

    # Work with the available files
    time.sleep(3)
    for file in files:
     
        file_path, file_type = get_file_type(file)

        valid_video_types = {"MP4", "AVI", "MKV", "MOV", "WMV", "FLV", "WEBM", "MPEG", "MPG", "OGV", "3GP", "MTS"}
        valid_image_types = {"PNG", "JPEG", "JPG", "BMP", "GIF", "TIFF", "WEBP"}

        try:
            # For Images
            if file_type in valid_image_types:
                handle_image(file, file_path)
            # For PDFs
            elif file_type == 'PDF':
                handle_pdf(file, file_path)
            # For videos
            elif file_type in valid_video_types:
                handle_video(file, file_path)

        except Exception as e:
            print(f"Invalid file {e}")

    # Convert extracted text to OCR
    do_ocr()    

    print("")

    outputs = "output_texts" # Folder of converted pngs
    files = sorted(os.listdir(outputs), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)

    # Loop thru every txt file containing extracted text and send to GPT
    for filename in files:  
        file_path = os.path.join(outputs , filename)  # Get the full path
        print("Calling GPT (Creating Notes)")
        text_call(file_path) # Send to GPT to make notes on

    # Read the content of the notes file
    with open("notes.txt", "r") as file:
        notes = file.read()
        notes = notes.replace("\n", "<br/>") # Replace new lines with line break element

    #create_pdf("notes.pdf", notes)

if __name__ == "__main__":
    main()
