from openai import OpenAI
import os
import re
import pandas as pd
import time

from config import COMPLETED_NOTES


# Set your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

# File deleter
def clear_output(folder_path):
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)


def get_embedding(text, model="text-embedding-3-small"):
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def create_outline(file_path, section_count):


    # Read input text from a file
    with open(file_path, "r", encoding="utf-8") as f:
        text_input = f.read()
    
    # Prompt for GPT to create an outline
    outline_prompt = f"""
    You are helping organize raw, out-of-order technical notes into a coherent teaching sequence.

    The original content is likely jumbled. Do **not** preserve its order.

    Your goal is to extract and organize the topics into a structured outline that reflects how a learner would progress through the material:
    - Begin with the most foundational concepts that do not rely on prior knowledge.
    - Then, introduce concepts that build directly on those foundations.
    - End with advanced topics that depend on earlier ones for full understanding.

    You must create exactly **{section_count}** top-level sections.

    Do not summarize or rephrase the input.
    Only output a clean outline in this format:

    1: [Title]
    -[Subtopic]
    -[Subtopic]
    2: [Title]
    ...

    Assume the goal is clarity, progression, and dependency-based ordering — not clustering by keyword or preserving the original structure.

    Raw Content:
    {text_input}
    """

    # Send to GPT
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a curriculum designer trained to organize raw technical content into a structured, teachable format. Your goal is to extract core topics, group related ideas, and order them in a clear learning progression from foundational to advanced concepts. Avoid following the input order. Instead, infer which concepts must be introduced early to support understanding of later ideas."},
            {"role": "user", "content": outline_prompt}
        ],
    )

    # Output result
    outline = completion.choices[0].message.content
    # print("\n--- Generated Outline ---\n")
    # print(outline)

    # Create an output directory
    os.makedirs(COMPLETED_NOTES, exist_ok=True)

    # Split the outline by top-level sections (e.g., "1.", "2.", etc.)
    sections = re.split(r'\n(?=\d+:\s)', outline.strip())

    # for sec in sections:
    #     print(sec)
    #     print("--")

    for sec in sections:
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        content = "\n".join(lines).strip()  # include title if you want
        
        # Make filename safe
        filename = f"{re.sub(r'[^a-zA-Z0-9]+', '_', title)[:50]}.txt"
        
        with open(os.path.join(COMPLETED_NOTES, filename), "w", encoding="utf-8") as f:
            f.write(content)

    # Build rows: each section gets its title and its block of content
    data = []
    for sec in sections:
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        text = "\n".join(lines[1:]).strip()
        embedding = get_embedding(sec)
        filename = f"{re.sub(r'[^a-zA-Z0-9]+', '_', title)[:50]}.txt"

        data.append({
            "filename": filename,
            "text": text,
            "embedding": embedding  # Placeholder
        })

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df.to_csv("debug_output.csv", index=False)

    return df