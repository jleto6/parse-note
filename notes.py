#!/usr/bin/env python3
import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import magic
import cv2
import numpy as np
import subprocess
import pandas as pd
from gpt_call import image_call, text_call
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph


def main():

    folder = "notes"
    files = os.listdir(folder) # List of files in notes folder 
    if ".DS_Store" in files:
        files.remove(".DS_Store")

    # Text file of all GPT outputs
    output_text = "notes.txt" 
    # Ensure the file exists by creating it if it doesnt
    open("notes.txt", "w").close()    

    # Folder of converted pngs
    pngs_folder = "converted_pngs" 
    os.makedirs(pngs_folder, exist_ok=True)

    # Work with the available files
    print("Available files:")
    for file in files:
        file_path = os.path.join(folder, file)  # Get full file path

        file_type = magic.from_file(file_path, mime=True) # Detects file type
        file_type = file_type.split("/")[-1]
        file_type = file_type.upper()
        print(f"{file_path} | {file_type}")

        try:
            # For Images
            valid_image_types = {"PNG", "JPEG", "JPG", "BMP", "GIF", "TIFF", "WEBP"}
            if file_type in valid_image_types:

                img = Image.open(file_path) # Open the current image 
                img = img.convert("RGBA") # Convert to RGBA

                # Create the output filename with a .png extention
                base_name = os.path.splitext(file)[0] + ".png"
                output_file = os.path.join(pngs_folder, base_name)
                img.save(output_file, "PNG")
                #print(f"Output file:{output_file}"
                
                '''
                if confidence low
                    img = img.resize((512, 512), Image.LANCZOS)
                '''
                
            # For PDFs
            elif file_type == 'PDF':
                images = convert_from_path(file_path) # Convert PDF pages to images
                images = images.resize((256, 256), Image.LANCZOS)
                # Save each page as a PNG in the output folder
                for i, image in enumerate(images):
                    image.save(os.path.join(pngs_folder, f"page_{i+1}.png"), "PNG")

        except Exception as e:
            print(f"Invalid file format {e}")

    
    # Folder of txt notes per image
    txt_folder = "output_texts" 
    os.makedirs(txt_folder, exist_ok=True)

    # Loop thru every output image
    counter = 1
    for file in os.listdir(pngs_folder):

        # Convert to OCR
        file_path = os.path.join(pngs_folder, file)
        image = Image.open(file_path) # Open image
        #text = pytesseract.image_to_string(image) # Convert image to text
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME) # Run OCR with detailed output
        #print(ocr_data)

        # Filter out NaN text and low-confidence words
        important_text = ocr_data[(ocr_data["text"].notna()) & (ocr_data["conf"] > 50)]
        # Extract the text as a list or single string
        extracted_text = " ".join(important_text["text"])

        #print(f"Extracted text: {extracted_text}")

        # Create a text file

        filename = f"output{counter}.txt"
        txt_path = os.path.join(txt_folder, filename)  # Create full file path inside the folder

        # Try to open the file in write mode with 
        with open(txt_path, "w", encoding="utf-8") as file:
            file.write(extracted_text + "\n")
            counter +=1

        # If low confidence, load to new file and use GPT Vision
        word_count = extracted_text.split() # Split text on spaces into a list
        word_count = len(word_count) # Get length of the list
        #print(f"Word count: {word_count}")

        valid_confidences = ocr_data[ocr_data["conf"] != -1]["conf"] # Extract the confidence levels that were valid
        average_confidence = valid_confidences.mean() # Calculate the mean of all of them to check if OCR was succesful
        #print(f"Average confidence: {average_confidence}")

        # If OCR had issues, call GPT Vision
        if word_count < 20 or average_confidence < 50:
            img = Image.open(file_path) # Open the current image 
            img = img.resize((512, 512), Image.LANCZOS) # Downscale it
            img.save(file_path)

            #print("Calling GPT Vision")

            response_content = "hi"
            #image_call(file_path)
            with open(txt_path, "a", encoding="utf-8") as file:
                file.write(response_content + "\n")
        # Else, send OCR text to GPT text
        else:
            print()

    # Loop thru every txt file containing notes
    for filename in os.listdir(txt_folder):  
        file_path = os.path.join(txt_folder, filename)  # Get the full path
        text_call(file_path) 

    # Create a PDF
    def create_pdf(filename, text):
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Split text into paragraphs (preserving newlines)
        for paragraph in text.split("\n\n"):  # Splits at paragraphs (double newlines for paragraphs)
            story.append(Paragraph(paragraph.replace("\n", "<br/>"), styles["Normal"]))
        # Create the pdf
        doc.build(story)

    # Read the content of the notes file
    with open("notes.txt", "r") as file:
        notes = file.read()

    create_pdf("notes.pdf", notes)

if __name__ == "__main__":
    main()
