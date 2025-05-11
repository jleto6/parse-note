from openai import OpenAI
import os
import re
import pandas as pd
import time
import math

from config import SECTIONS, DISTILLED_DOC
from nlp.embedding_utils import get_embedding, get_embeddings_batch
from extraction.file_utils import clear_output

# Set your OpenAI API key
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI
deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek


def create_outline(file_path):

    # Read input text from a file
    with open(file_path, "r", encoding="utf-8") as f:
        text_input = f.read()
    
    # Prompt for GPT to create an outline
    outline_prompt = f"""
    You are transforming raw, unordered technical content into a **teaching-aligned semantic index** optimized for chunk-based retrieval in a Retrieval-Augmented Generation (RAG) system.

    This is not a summary or a human-readable outline. It is a machine-usable structure for embedding and retrieval.

    Your job is to:
    1. Extract exact, high-signal elements from the text. This includes:
    - Technical terms or labels
    - Variable names, identifiers, and acronyms
    - Numeric formats and constants
    - Equations, scientific notation, symbolic expressions
    - Structured examples, pseudocode, or formulas
    - Code-like syntax, command names, or config values
    - Anything that might be searched directly or used in semantic matching

    2. Group these elements into semantically distinct sections based on conceptual closeness.
    3. Order those sections in the sequence a learner would need to understand them—from foundational to advanced, based on dependencies.

    Each section must:
    - Use a **keyword-rich, descriptive title** that reflects search intent.
    - Contain **3–7 bullet points**, each being a **direct extraction** from the raw input.
    - Include raw expressions, equations, formats, phrases, or code as-is.
    - Avoid paraphrasing or smoothing of language.
    - Focus entirely on making each section dense and unique for semantic embedding.

    Do not:
    - Summarize
    - Explain
    - Reword technical content
    - Split variants of the same concept across multiple sections
    - Follow the input order or keyword clusters—only use learning progression and conceptual distinctiveness

    Output format:

    1: [Section Title with technical keywords]
    - Raw term or variable name
    - Full equation or expression from input
    - Identifier or phrase used literally in the source
    - Format string, code snippet, or symbolic reference
    - ...

    2: [Next Section Title]
    - ...

    Return only the structured index. No explanation or notes.

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

    # Result
    outline = completion.choices[0].message.content

    # Save the outline as the distilled doc
    with open(DISTILLED_DOC, 'w', encoding="utf-8") as f:
        f.write(outline)

    os.makedirs(SECTIONS, exist_ok=True) # Create an output directory

    sections = re.split(r'\n(?=\d+:\s)', outline.strip())  # Split the outline by top-level sections (e.g., "1.", "2.", etc.)

    # for sec in sections:
    #     print(sec)
    #     print("--")

    for sec in sections:
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        content = "\n".join(lines).strip()  # include title if you want
        
        # Make filename safe
        filename = f"{re.sub(r'[^a-zA-Z0-9]+', '_', title)[:50]}.txt"
        
        with open(os.path.join(SECTIONS, filename), "w", encoding="utf-8") as f:
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