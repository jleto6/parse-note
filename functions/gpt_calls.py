import base64
from openai import OpenAI
import openai
import os
import markdown

from flask_socketio import SocketIO
import json

# Use Deepseek
deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  )

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

previous_content = ""
string_buffer = ""
answer_buffer = ""

# Check for section end function
def end_section(string_buffer):
    from app import socketio
    if "<!-- END_SECTION -->" in string_buffer:
        string_buffer = markdown.markdown(string_buffer) # Convert to HTML
        socketio.emit("update_notes", {"notes": string_buffer, "refresh": True})

def end_answer(answer_buffer):
    from app import socketio
    if "<!-- END_SECTION -->" in answer_buffer:
        answer_buffer = markdown.markdown(answer_buffer) # Convert to HTML
        socketio.emit("answers", {"answer": answer_buffer, "refresh": True})

# -----------------------------------------------
# GPT Functions
# -----------------------------------------------

# IMAGE CALL
def image_call(file_path):
    # Get the Base64 string of the file
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    base64_image = encode_image(file_path)

    prompt1 = "Whats in this image?"

    # GPT Call
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt1,
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
    return response_content


# LOGICALLY ORDER FILES
def order_files(files):
    # Format the list into a readable string for GPT
    file_list_text = "\n".join(f"- {f}" for f in files)

    content = f"""Here is a list of filenames:
    {file_list_text}

    Ignore any numbers, prefixes, or similarities in filename style. Focus only on the topic meaning.

    First, infer the general subject these files relate to.

    Then, imagine you are designing a learning guide for someone starting with no prior knowledge:
    - Group files into clusters of related topics.
    - Within each group, arrange from most basic to most advanced ideas.
    - Order the groups themselves in a way that builds up understanding naturally from simple foundations to more complex concepts.

    Think carefully about learning dependencies — what someone must understand first before moving to the next idea.

    **Return only the reordered list of original filenames, one per line, with no dashes, numbering, bullets, or extra symbols. Only the filenames exactly as they appear.**
    """

    # Ask GPT to reorder the list conceptually
    response = openai_client.chat.completions.create(
        model="o4-mini",
        messages=[
            {
                "role": "user",
                "content": content
            }
        ]
    )

    # Extract and return the response text (assuming it's just a list)
    ordered_text = response.choices[0].message.content

    # print(ordered_text)

    filenames_array = ordered_text.splitlines()
    return filenames_array




  