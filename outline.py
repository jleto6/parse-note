from openai import OpenAI
import os
import re
import pandas as pd
import time

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

def create_outline(file_path):


    # Read input text from a file
    with open(file_path, "r", encoding="utf-8") as f:
        text_input = f.read()
    
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
    os.makedirs("sections", exist_ok=True)
    clear_output("sections")

    # Split the outline by top-level sections (e.g., "1.", "2.", etc.)
    sections = re.split(r'\n(?=\d+:\s)', outline.strip())

    # Show sections
    for sec in sections:
        print(sec)
        print("--")

    # Make a folder to store the sections
    os.makedirs("sections", exist_ok=True)

    for sec in sections:
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        content = "\n".join(lines).strip()  # include title if you want
        
        # Make filename safe
        filename = f"{re.sub(r'[^a-zA-Z0-9]+', '_', title)[:50]}.txt"
        
        with open(os.path.join("sections", filename), "w", encoding="utf-8") as f:
            f.write(content)

    # Build rows: each section gets its title and its block of content
    data = []
    for sec in sections:
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        filename = f"{re.sub(r'[^a-zA-Z0-9]+', '_', title)[:50]}.txt"
        embedding = get_embedding(sec)
        data.append({
            "filename": filename,
            "content": content,
            "embedding": embedding  # Placeholder
        })

    # Convert to DataFrame
    df = pd.DataFrame(data)

    return df

# df = create_outline("raw_text.txt")
# print(df)