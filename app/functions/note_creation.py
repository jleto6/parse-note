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

from functions.gpt_functions import end_answer, end_section
from config import COMPLETED_NOTES_INDEX, FILE_EMBEDDINGS, COMPLETED_NOTES_FILE, COMPLETED_NOTES


def strip_html(text):
    return re.sub(r'<[^>]*>', '', text)

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

previous_content = ""
string_buffer = ""
answer_buffer = ""
i = 0

def get_embedding(text, model="text-embedding-3-small"):
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding

# Function To Embed a File
def embed_file(content_path):
    # Read the entire content of the file as a single string
    with open(content_path, "r", encoding="utf-8") as file:
        full_text = file.read().strip()

    # Generate embedding for the full text
    response = openai_client.embeddings.create(
        input=[full_text],
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    return embedding

# Function To Embed Text
def embed_text(content):

    # Generate embedding for the full text
    response = openai_client.embeddings.create(
        input=[content],
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    return embedding


# -----------------------------------------------
# GENERATE THE NOTES
# -----------------------------------------------

def note_creation(content, outline_df):

    output_buffer = ""

    print("Calling GPT (Creating Notes)")

    global i

    from app import socketio

    # RAG
    current_embedding = embed_file(content)
    
    # outline_df['embedding'] = outline_df['embedding'].apply(ast.literal_eval) # Convert the embedding column from a string back into a list of floats

    # Function to compare two vectors similarity
    def similarity_score(page_embedding, question_embedding):
        return np.dot(page_embedding, question_embedding) # Return their dot product (similarity score)
    
    # Compute similarity scores for each chunk
    outline_df["score"] = outline_df["embedding"].apply( # Create a new 'score' column for each chunk
        lambda file_embedding: similarity_score(file_embedding, current_embedding) # Get a similarity score for each
    )

    # print(file)

    top_chunk = outline_df.sort_values("score", ascending=False).head(1) # sort the DataFrame by similarity score in descending order
    # print(top_chunk)
    most_similar_file_text = top_chunk["text"].iloc[0] # Get the text of the top_chunk
    most_similar_file_name = top_chunk["filename"].iloc[0] # Get the filename the top_chunk came from
    

    current_file = os.path.join(COMPLETED_NOTES, most_similar_file_name)

    print(top_chunk["score"].iloc[0], end =" ") 
    print(f"The most similar file to the current file is: {most_similar_file_name}")

    global previous_content
    # Read the content of the current file
    with open(content, "r") as file:
        file_content = file.read()

        # print("===============================")
        # print(file_content)
        # print("===============================")


        previous_content += file_content # Store all read files in memory so GPT knows whats covered

    # GPT Call
    completion = openai_client.chat.completions.create(

        # model="deepseek-chat",
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI that extracts and reconstructs complete, highly structured, deeply detailed technical or academic documentation from source material. "
                    "This is not summarization or simplification. Your task is to capture all relevant information, including causal logic, conceptual dependencies, "
                    "step-by-step processes, and contextual relationships. Do not omit or gloss over complexity under any circumstance. "
                    "It is extremely important that you stay *very* close to the original provided text. Maintain fidelity to wording, structure, and phrasing unless clarity or formatting demands a minimal adjustment."
                )
            },
            {
            "role": "user",
            "content": f"""
            Write deeply detailed, structured documentation in valid HTML, intended for insertion into a Jinja template. Output raw HTML—no Markdown, code fences, or formatting artifacts. Use <p style="color:whitesmoke;"> for all body text. Bold all key terms using <strong>. All code or syntax references should use <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;">.

            <strong>Structural Rules:</strong>  
            - Use exactly one <h1> tag for the overall topic. Do not generate more than one.  
            - Use at most one or two <h3> subheadings if essential for clarity.  
            - Use <ol> for any step-by-step processes, ordered procedures, or sequences—<strong>always</strong>.  
            - Use <ul> only if content clearly involves categories or non-ordered groupings.  
            - Avoid excessive lists—favor <p> for general explanation.  
            - Insert '<!-- END_SECTION -->' after every HTML block.

            <strong>Clarity & Integration Rules:</strong>  
            - When a new concept or term appears, briefly define it and explain its role or relevance within the system or topic.  
            - If content contains examples, scenarios, or data, include them—they may replace long explanations if they clarify the point.  
            - Seamlessly insert brief (1–2 sentence) insights only when needed to explain:  
            1. Why a concept matters  
            2. How it fits into the system  
            3. How it builds on prior content  

            Do not introduce or summarize. Do not address the reader. Avoid filler or framing statements.

            <strong>Heading Rule:</strong> You must insert exactly one <h1> heading at the beginning of the output to represent the main topic. There must be one and only one <h1> tag. Do not include multiple <h1> tags under any circumstances. You may optionally include one or two <h3> subheadings if absolutely necessary, but avoid them unless essential for clarity or structure. Treat the rest of the content as a single section under that heading.

            The following is a summary of previously covered material (for context only—do not repeat it):
            {previous_content}

            Use the structure of the most similar file as a guide for how to organize this section. Do not copy its content, but follow its general flow and topic segmentation when possible. If parts of the structure don’t apply, skip them. If new topics appear in the new material, insert them logically where they fit best.

            Here is the structural reference you may loosely follow:
            {most_similar_file_text}

            You are updating the existing generated notes below to incorporate new material.  
            The goal is to append and integrate the new content meaningfully—not to rewrite the previous content.  
            Preserve the structure, wording, and HTML of what has already been written as much as possible.  
            Use the new content to improve or clarify earlier explanations if needed, but do not discard or simplify them.

            Append and integrate this new content:
            {content}

            The existing content is:
            {file_content}
            """
        },
        ],
        stream=True
    )

    global string_buffer

    open(current_file, "w", encoding="utf-8") # Clear/open the file in

    for chunk in completion:
        try:
            delta = chunk.choices[0].delta
            content = delta.content if delta and hasattr(delta, "content") else None

            if content:
                string_buffer += content
                output_buffer += content
                with open(current_file, "a", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                end_section(string_buffer)
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")

    socketio.emit("update_notes", {"notes" : "<br/><br/>"})  # Emit linebreaks at the end

    # Get genereated notes info
    output_text = strip_html(output_buffer) # Strip the HTML content from the GPT output to get the text
    current_file_name = os.path.basename(current_file) # Get the filename from the current file
    embedded_notes = embed_text(output_buffer) # Embed what gpt just created

    # Create DataFrame from existing CSV, remove outdated row (if present), and add updated entry
    if not(os.path.isfile(FILE_EMBEDDINGS)): # Check if the CSV doesnt exist 
        df = pd.DataFrame(columns=["filename", "text", "embedding"]) # If it doesnt, write headers
    else:
        df = pd.read_csv(FILE_EMBEDDINGS) # If it does, open it

    df = df[df["filename"] != current_file_name] # Remove any existing embedding for the current file to avoid duplicates
    df.loc[len(df)] = [current_file_name, output_text, str(embedded_notes)] # Add the updated embedding for the current file

    # Append to the CSV
    df.to_csv(FILE_EMBEDDINGS, index=False) # Write the DF to CSV at location FILE_EMBEDDINGS
        