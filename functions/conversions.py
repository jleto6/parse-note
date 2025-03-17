import os
from pdf2image import convert_from_path
from PIL import Image
import magic
import subprocess

# Uploaded Files
folder = "notes"
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
os.makedirs(wavs_folder, exist_ok=True) # Make folder if it doesnt exist

def handle_video(file, file_path):
    base_name = os.path.splitext(file)[0] + ".wav" # Create the output filename with a .wav extension
    output_file = os.path.join(wavs_folder, base_name) # Create full file path by joining 'wavs folder' and file name
    subprocess.run(["ffmpeg", "-i", file_path, "-ac", "1", "-ar", "16000", output_file, "-y"], # Convert video file to audio file and save it
               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) # Supress output other than errors
    
for file in files:
    file_path, file_type = get_file_type(file)
    handle_video(file, file_path)

    

    