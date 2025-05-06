import os
import time
import pandas as pd
import glob
import re

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

from functions.gpt_functions import order_files
from functions.note_creation import note_creation
from functions.file_handler import handle_image, handle_pdf, get_file_type, handle_video, clear_output, split_text
from functions.topic_modelling import nlp
from functions.question_manager import embed_corpus
from functions.outline import create_outline

from app import socketio, app   
from threading import Thread
import threading

from config import TOPIC_OUTPUTS_DIR, NOTE_INPUTS_DIR, RAW_TEXT, COMPLETED_NOTES, FILE_EMBEDDINGS, COMPLETED_NOTES_FILE

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Run App
def run_flask():
    print("Flask server starting on http://127.0.0.1:5000")
    app.run(debug=False, use_reloader=False)  # Starts Flask but doesn't block main.py
# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Timer
stop_timer = threading.Event() # Stop event
def timer():
    start_time = time.time()
    while not stop_timer.is_set():
        elapsed = time.time() - start_time
        print(f"\rElapsed time: {elapsed:.2f} seconds")
        socketio.emit("timer", {"time" : elapsed})
        time.sleep(1)
# Start the timer thread
timer_thread = threading.Thread(target=timer)
timer_thread.start()

# -----------------------------------------------
#  Main
# -----------------------------------------------

def main():

    # Clear old outputs
    clear_output(TOPIC_OUTPUTS_DIR)
    clear_output(RAW_TEXT)
    clear_output(COMPLETED_NOTES)


    try: 
        clear_output(FILE_EMBEDDINGS)
    except:
        pass

    # Uploaded Files
    folder = NOTE_INPUTS_DIR
    files = sorted(os.listdir(folder), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)

    if ".DS_Store" in files:
        files.remove(".DS_Store")
    if not files:
        print("No available files in the folder.")
        while not files:
            #print("Waiting for files.")
            files = sorted(os.listdir(folder), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)
    else:
        print("Files found:", files)
        file_flag = False
        if len(files) == 1:
            file_flag = True
    print("")

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

    time.sleep(3)

    # Embed the extracted RAW TEXT
    embed_corpus(RAW_TEXT)

    # Signal the timer thread to stop (processing done)
    stop_timer.set()
    # Wait for the timer thread to finish
    timer_thread.join()

    # Chunk sequentially
    chunk_count = split_text(RAW_TEXT, 500)
    print(chunk_count)
    ordered_files = sorted(os.listdir(TOPIC_OUTPUTS_DIR), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)

    # Creata an outline from the raw text and return a df with info
    df = create_outline(RAW_TEXT, chunk_count)

    # # If only one file, no topic modelling needed
    # if file_flag:
    #     split_text(RAW_TEXT, 500)
    #     ordered_files = sorted(os.listdir(TOPIC_OUTPUTS_DIR), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)
    # else:

    #     # Try NLP if more than one file
    #     print("Topic Modelling")
    #     try:
    #         # Topic Modeling For Large Input
    #         topic_summary = nlp() # Perform NLP and get its data
    #         files = os.listdir(TOPIC_OUTPUTS_DIR) # Loop through topic text files
    #         ordered_files = order_files(files, topic_summary) # Order the topics in a logical order with GPT
    #         print(ordered_files)
    #     # If Too Small For Topic Modelling, Just Split
    #     except TypeError as e:
    #         print(e)
    #         split_text(RAW_TEXT, 500)
    #         ordered_files = sorted(os.listdir(TOPIC_OUTPUTS_DIR), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)
    #         # print("-------------")
    #         # print(ordered_files)
    #         # time.sleep(500)

    print("--------------")
    print("Creating Notes")
    print("--------------")


    # Create notes on files
    for file in ordered_files:
        note_creation(f"{TOPIC_OUTPUTS_DIR}/{file}", df) # Send topics GPT to make notes on

    # # Read the content of the notes file
    # with open(COMPLETED_NOTES, "r") as file:
    #     notes = file.read()
    #     notes = notes.replace("\n", "<br/>") # Replace new lines with line break element

if __name__ == "__main__":
    main()
