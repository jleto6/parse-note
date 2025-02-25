import base64
from openai import OpenAI
import openai

openai.api_key = "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"

# -----------------------------------------------
# GPT Function
# -----------------------------------------------

# GPT Prompt
prompt = """
        Write clear and detailed notes in full sentences without bullet points. Cover each slide one at a time, fully explaining the material. Break down concepts step by step in a way that is easy to follow and understand. Use natural, straightforward language without third-person narration or unnecessary formal phrasing. The notes should be detailed and easy to study as they are, without needing to be rewritten or reorganized.    
        """
prompt1 = "Whats in this image?"

def text_call(content):

    # Step 1: Read the content of the file
    with open("ocr.txt", "r") as file:
        file_content = file.read()

    # GPT Call
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": file_content}
        ]
    )
    # Process GPT Response ee
    response_content = completion.choices[0].message.content
    with open("output.txt", "a", encoding="utf-8") as file:
            file.write(response_content + "\n")  # Appends text to output file

def image_call(file_path):

    # Get the Base64 string of the file
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    base64_image = encode_image(file_path)

    # GPT Call
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ],
    )

    # Process GPT Response
    response_content = completion.choices[0].message.content

    with open("output.txt", "a", encoding="utf-8") as file:
            file.write(response_content + "\n")  # Appends text to output file
    #print(f"{response_content}")

    return    

  