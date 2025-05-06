import base64
from openai import OpenAI
import openai
import os
import markdown
from flask_socketio import SocketIO
import json

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

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
    if "<!-- END_ANSWER -->" in answer_buffer:
        answer_buffer = markdown.markdown(answer_buffer) # Convert to HTML
        socketio.emit("answers", {"answer": answer_buffer, "refresh": True})

# -----------------------------------------------
# GPT Functions
# -----------------------------------------------

# IMAGE CALL
def image_call(file_path):
    # Get the Base64 string of the file
    
    # Function to encode the image
    def encode_image(image_source):
        if hasattr(image_source, "read"):  # it's a file-like object
            return base64.b64encode(image_source.read()).decode("utf-8")
        else:  # it's a file path
            with open(image_source, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

    base64_image = encode_image(file_path)

    prompt = (
    "Look at this image and do the following:\n"
    "1. If the image is a diagram, chart, or graph, analyze it in detail. "
    "Describe the layout, label each axis, summarize the data trends, and explain what insights can be drawn from it.\n"
    "2. If the image contains handwritten notes, transcribe the text as accurately as possible. "
    "Include any formatting, headers, or structure you can infer.\n"
    "If you're unsure what kind of image it is, describe it first, then proceed with the appropriate action."
    )

    # GPT Call
    completion = openai_client.chat.completions.create(
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
    return response_content


# LOGICALLY ORDER FILES
def order_files(files, topic_summary):
    # Format filenames as a bulleted list
    file_list_text = "\n".join(f"- {f}" for f in files)

    # Build topic summaries matched to each file
    topic_summaries = ""
    for fname in files:
        match = topic_summary[topic_summary["Filename"] == fname]
        if not match.empty:
            row = match.iloc[0]
            topic_summaries += f"\nFilename: {fname}\nKeywords: {row['Keywords']}\nSnippet: {row['Representative_Snippet'][:300]}\n"

    # Compose full prompt with both filename list and summaries
    content = f"""Here is a list of filenames:
    {file_list_text}

    Each filename has an associated topic summary below. Use the keywords and snippet to better understand the topic meaning:

    {topic_summaries}

    Ignore any numbers, prefixes, or similarities in filename style. Focus only on the topic meaning.

    First, infer the general subject these files relate to.

    Then, imagine you are designing a learning guide for someone starting with no prior knowledge:
    - Group files into clusters of related topics.
    - Within each group, arrange from most basic to most advanced ideas.
    - Order the groups themselves in a way that builds up understanding naturally from simple foundations to more complex concepts.

    Think carefully about learning dependencies — what someone must understand first before moving to the next idea.

    **Return only the reordered list of original filenames, one per line, with no dashes, numbering, bullets, or extra symbols. Only the filenames exactly as they appear.**
    """

    print(content)

    # Ask GPT to reorder the list conceptually
    response = openai_client.chat.completions.create(
        model="o4-mini",
        messages=[
            {"role": "user", "content": content}
        ]
    )

    # Extract filenames from output
    ordered_text = response.choices[0].message.content
    filenames_array = ordered_text.splitlines()

    return filenames_array



  