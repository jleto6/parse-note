import os
from PIL import Image
import magic
import pytesseract
import re
from io import BytesIO

from nlp.gpt_utils import image_call
from config import RAW_TEXT

def ocr(image):

    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME) # Run OCR with detailed output
    #print(ocr_data)

    # Getting text from OCR data
    important_text = ocr_data[(ocr_data["text"].notna()) & (ocr_data["conf"] > 50)] # Filter out NaN text and low-confidence words
    extracted_text = " ".join(important_text["text"]) # Extract the text as a list or single string
    #print(f"Extracted text: {extracted_text}")

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
        # img = Image.open(image) # Open the current image 
        image = image.resize((512, 512), Image.LANCZOS) # Downscale it
        # image.save(image)

        # Convert PIL Image to in-memory PNG for GPT Vision
        image_io = BytesIO()
        image.save(image_io, format="PNG")
        image_io.seek(0)
        image = image_io  # overwrite the original variable

        print(f"Calling GPT Vision on {image}")
        response_content = image_call(image)

        with open(RAW_TEXT, "a", encoding="utf-8") as file:
            file.write(response_content + "\n")

    # Else write OCR result to file
    else:
        # Try to open the file in write mode 
        with open(RAW_TEXT, "a", encoding="utf-8") as file:
            file.write(extracted_text + "\n\n")
