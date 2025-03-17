import os
import time
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

from functions.ocr import do_ocr
from functions.gpt_call import image_call, text_call
from functions.conversions import handle_image, handle_pdf, get_file_type, handle_video

from app import get_notes, read_notes
from app import app
from threading import Thread
import threading

def run_flask():
    app.run(debug=True, use_reloader=False)  # Starts Flask but doesn't block main.py

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Start the file watcher in a background thread
threading.Thread(target=read_notes, daemon=True).start()

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

# MAIN
def main():
    # Uploaded Files
    folder = "notes"
    files = os.listdir(folder) # List of files in notes folder 
    if ".DS_Store" in files:
        files.remove(".DS_Store")
    if "test_notes" in files:
        files.remove("test_notes")

    output_text = "notes.txt"   # Text file of all GPT note outputs
    open("notes.txt", "w").close()  # Ensure the file exists by creating it if it doesnt

    # Work with the available files
    time.sleep(3)
    print("\nAvailable files:")
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
    # Loop thru every txt file containing extracted text and send to GPT
    for filename in os.listdir("output_texts" ):  
        file_path = os.path.join("output_texts" , filename)  # Get the full path
        time.sleep(5)
        print("Calling GPT (Creating Notes)")
        text_call(file_path) # Send to GPT to make notes on

    # Read the content of the notes file
    with open("notes.txt", "r") as file:
        notes = file.read()
        notes = notes.replace("\n", "<br/>") # Replace new lines with line break element

    #print(f"Notes: {notes}")
    #update_notes(notes)
    #create_pdf("notes.pdf", notes)

if __name__ == "__main__":
    main()
