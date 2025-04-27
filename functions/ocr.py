import os
from PIL import Image
import magic
import pytesseract
import re

from functions.gpt_calls import image_call

def do_ocr(image):

    # Path of txt for outputting
    txt_path = "text.txt"

    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME) # Run OCR with detailed output
    #print(ocr_data)

    # Getting text from OCR data
    important_text = ocr_data[(ocr_data["text"].notna()) & (ocr_data["conf"] > 50)] # Filter out NaN text and low-confidence words
    extracted_text = " ".join(important_text["text"]) # Extract the text as a list or single string
    #print(f"Extracted text: {extracted_text}")

    # Try to open the file in write mode 
    with open(txt_path, "a", encoding="utf-8") as file:
        file.write(extracted_text + "\n\n")

    # Get word count
    word_count = extracted_text.split() # Split text on spaces into a list
    word_count = len(word_count) # Get length of the list
    #print(f"Word count: {word_count}")

    # Get confidence levels
    valid_confidences = ocr_data[ocr_data["conf"] != -1]["conf"] # Extract the confidence levels that were valid
    average_confidence = valid_confidences.mean() # Calculate the mean of all of them to check if OCR was succesful
    #print(f"Average confidence: {average_confidence}")

    # If low OCR data, call GPT Vision
    if word_count < 20 or average_confidence < 50:
        img = Image.open(image) # Open the current image 
        img = img.resize((512, 512), Image.LANCZOS) # Downscale it
        img.save(image)

        print(f"Calling GPT Vision on {image}")
        response_content = ""
        image_call(image)
        with open(txt_path, "a", encoding="utf-8") as file:
            file.write(response_content + "\n")
