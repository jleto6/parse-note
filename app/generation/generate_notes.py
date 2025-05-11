import base64
from openai import OpenAI
import os
import markdown
from flask_socketio import SocketIO
import json
import csv
import numpy as np
import pandas as pd
import ast
import re

from nlp.gpt_utils import end_answer, end_section
from nlp.embedding_utils import embed_text, similarity_score
from config import COMPLETED_NOTES_FILE, SECTIONS

def strip_html(text):
    return re.sub(r'<[^>]*>', '', text)

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

previous_content = ""
string_buffer = ""
answer_buffer = ""
i = 0

# -----------------------------------------------
# GENERATE NOTES
# -----------------------------------------------

def  create_notes(current_file, df_outline):

    print("Calling GPT (Creating Notes)")

    row = df_outline[df_outline["filename"] == current_file].iloc[0]
    outline = row["text"]

    current_file = os.path.join(SECTIONS, current_file)

    with open(current_file, 'r', encoding="utf-8") as f:
        text = f.read()

    completion = openai_client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI that extracts and reconstructs complete, highly structured, deeply detailed technical or academic documentation from source material. "
                    "This is not summarization or simplification. Your task is to capture all relevant information—causal logic, conceptual dependencies, step-by-step processes, data references, and structural relationships. "
                    "You must remain faithful to the original *text*. Do not omit complexity. Stay extremely close to the original phrasing unless clarity requires minimal adjustment. "
                    "The 'outline' is only a suggested organizational guide; use it only if it helps. It does not override or filter what must be extracted from the content. "
                    "Assume the reader has *no prior knowledge*. Never skip definitions, abbreviations, or explanations. Build every concept clearly and completely as it appears in the input."
                )
            },
            {
                "role": "user",
                "content": f"""
    Write deeply detailed, structured documentation in valid HTML for Jinja insertion. Output raw HTML—no Markdown, no formatting artifacts. Use <p style="color:whitesmoke;"> for all body text. Bold key terms with <strong>. Use <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;"> for code or syntax references.

    <strong>Formatting Rules:</strong>
    - Use exactly one <h1> to state the main topic.
    - Use <h3> for optional subsections only if necessary for clarity.
    - Use <ol> for procedures or ordered steps.
    - Use <ul> for grouped items or non-sequential info.
    - Prefer <p> over lists unless a list is clearly warranted.
    - Add '<!-- END_SECTION -->' after each complete HTML block.

    <strong>Clarity Rules:</strong>
    - Do not assume any prior knowledge.
    - Define every concept or term when it first appears and explain its relevance.
    - Include examples, formulas, or data when they clarify meaning.
    - Insert short (1–2 sentence) insights only if needed to explain:
    1. Why it matters
    2. How it fits into the system
    3. How it connects to earlier parts

    <strong>Heading Rule:</strong>
    You must insert one and only one <h1> tag at the beginning. Use at most two <h3> tags. Treat everything else as belonging under the <h1>.

    The outline below is a suggested structure. Use it only if it helps with organization:
    {outline}

    The content below is the authoritative source. Extract all meaningful structure and detail from this:
    {text}
    """
            },
        ],
        stream=True
    )

    global string_buffer
    open(current_file, "w", encoding="utf-8") # Clear/open the file in

    from app import socketio
    for chunk in completion:
        try:
            delta = chunk.choices[0].delta
            write_content = delta.content if delta and hasattr(delta, "content") else None

            if write_content:
                string_buffer += write_content
                with open(current_file, "a", encoding="utf-8") as f:
                    f.write(write_content)
                    f.flush()
                end_section(string_buffer)
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")

    socketio.emit("update_notes", {"notes" : "<br/><br/>"})  # Emit linebreaks at the end
