from openai import OpenAI
import os
import re
import pandas as pd
import time
import math

from config import COMPLETED_NOTES
from nlp.embedding_utils import get_embedding
from extraction.file_utils import clear_output

# Set your OpenAI API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI
deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek


def create_outline(file_path, section_count):

    print(section_count)

    # Read input text from a file
    with open(file_path, "r", encoding="utf-8") as f:
        text_input = f.read()
    
    # Prompt for GPT to create an outline
    outline_prompt = f"""
    You are helping organize raw, out-of-order technical notes into a coherent teaching sequence optimized for Retrieval-Augmented Generation (RAG) systems.

    The original content is likely jumbled. Do **not** preserve its order.

    Your goal is to extract and organize topics into a clearly structured outline that reflects how a learner would progress through the material:
    - Start with foundational topics requiring no prior knowledge.
    - Progress to intermediate concepts that build on those foundations.
    - End with advanced ideas requiring deeper understanding.

    Only include distinct top-level sections. Each section must represent a clearly non-overlapping concept or skill. Do not split a topic across multiple sections. Only create separate sections when topics are fundamentally different in purpose or function. Closely related subtopics — like variations of the same concept (e.g., cache types or policies) — must be grouped together into a single, comprehensive section for that concept. Do not create multiple sections for different configurations or options of the same system.

    There are {section_count} content chunks. You must generate **no more than {math.floor(section_count/2)} sections**. Fewer sections are allowed if and only if merging results in highly distinct and semantically strong groupings. Exceeding {section_count} sections will break alignment with chunk-based retrieval and is not allowed.

    Each section must:
    - Use a specific, keyword-rich title that would match real-world technical search queries.
    - Contain 2–4 bullet points with detailed, descriptive language.
    - Repeat or reinforce key terminology from the section title and chunk contents.
    - Be semantically focused — each section should be easy to embed and retrieve on its own.

    Do **not** summarize or rephrase the raw content. Focus entirely on extracting structure and topics.
    Only output a clean outline in this format:

    1: [Section Title with keywords]
    - Bullet point with relevant terminology
    - Another bullet point with concepts or phrases that would be searched
    2: [Next Section Title]
    ...

    Do not cluster by keyword or follow the original order. Optimize purely for clarity, distinctiveness, teaching progression, and RAG-friendly retrieval alignment.

    Raw Content:
    {text_input}
    """

    # Send to GPT
    completion = openai_client.chat.completions.create(
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
    # df.to_csv("debug_output.csv", index=False)

    return df