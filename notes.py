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
from gpt_call import image_call


def main():

    folder = "notes"
    files = os.listdir(folder) # List of files in notes folder 
    if ".DS_Store" in files:
        files.remove(".DS_Store")

    # Folder of converted pngs
    output_folder = "converted_pngs" 
    os.makedirs(output_folder, exist_ok=True)

    # Text file of all extracted data
    output_text = "output.txt" 
    # Ensure the file exists by creating it if it doesnt
    open("output.txt", "a").close()

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
                output_file = os.path.join(output_folder, base_name)
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
                    image.save(os.path.join(output_folder, f"page_{i+1}.png"), "PNG")

        except Exception as e:
            print(f"Invalid file format {e}")

    
    # Loop thru every output image
    for file in os.listdir(output_folder):

        # Convert to OCR
        file_path = os.path.join(output_folder, file)
        image = Image.open(file_path) # Open image
        #text = pytesseract.image_to_string(image) # Convert image to text
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME) # Run OCR with detailed output
        print(ocr_data)

        # Append text to txt file
        #with open("ocr.txt", "a", encoding="utf-8") as file:
            #file.write(text + "\n")

        # If low confidence, load to new file and use GPT Vision
     
        #image_call("ocr.txt")   

      
        
     


if __name__ == "__main__":
    main()
