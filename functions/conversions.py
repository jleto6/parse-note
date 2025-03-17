import os
from pdf2image import convert_from_path
from PIL import Image
import magic

# Uploaded Files
folder = "notes"
files = os.listdir(folder) # List of files in notes folder 
if ".DS_Store" in files:
        files.remove(".DS_Store")

# Folder of converted pngs
pngs_folder = "converted_pngs" 

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

    # Create the output filename with a .png extention
    base_name = os.path.splitext(file)[0] + ".png"
    output_file = os.path.join(pngs_folder, base_name)
    img.save(output_file, "PNG")
    #print(f"Output file:{output_file}"

# Handle PDFs
def handle_pdf(file, file_path):

    images = convert_from_path(file_path) # Convert PDF pages to a list of images
    # Save each page as a PNG in the output folder
    for i, image in enumerate(images):
        image.save(os.path.join(pngs_folder, f"page_{i+1}.png"), "PNG")

# Handle Videos
def video(file, file_path):
    file_path, _ = get_file_type(file)

#for file in files:
 #   video(file)

    