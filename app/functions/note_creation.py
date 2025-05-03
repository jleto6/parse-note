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
from config import COMPLETED_NOTES_INDEX, FILE_EMBEDDINGS, DATA_DIR


def strip_html(text):
    return re.sub(r'<[^>]*>', '', text)

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

previous_content = ""
string_buffer = ""
answer_buffer = ""

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

def note_creation(content):

    output_buffer = ""

    print("Calling GPT (Creating Notes)")


    from app import socketio

    # RAG
    current_embedding = embed_file(content)

    i = 0
    # Try to open CSV file to compare current embedding to prior embeddings
    try:
        # Load the saved CSV file as a pandas DataFrame
        corpus_df = pd.read_csv(FILE_EMBEDDINGS)
        corpus_df['embedding'] = corpus_df['embedding'].apply(ast.literal_eval) # Convert the embedding column from a string back into a list of floats

        # Function to compare two vectors similarity
        def similarity_score(page_embedding, question_embedding):
            return np.dot(page_embedding, question_embedding) # Return their dot product (similarity score)

        # Compute similarity scores for each chunk
        corpus_df["score"] = corpus_df["embedding"].apply( # Create a new 'score' column for each chunk
            lambda file_embedding: similarity_score(file_embedding, current_embedding) # Get a similarity score for each
        )
        top_chunk = corpus_df.sort_values("score", ascending=False).head(1) # sort the DataFrame by similarity score in descending order
        # print(top_chunk)
        most_similar_file_text = top_chunk["text"].iloc[0] # Get the text of the top_chunk
        most_similar_file_name = top_chunk["filename"].iloc[0] # Get the filename the top_chunk came from

        print(top_chunk["score"].iloc[0])

        if top_chunk["score"].iloc[0] < 0.4:
            print("# Low similarity – create a new file")
            i += 1
            current_file = f"{COMPLETED_NOTES_INDEX}_{i}.txt"

        else:
            print(f"The most similar file to the current file is: {most_similar_file_name}")
            current_file = os.path.join(DATA_DIR, most_similar_file_name)
        

    except:
        # No CSV file to compare to yet
        # print("No CSV file to compare to yet")
        current_file = f"{COMPLETED_NOTES_INDEX}_{i}.txt"
        pass

    

    # GPT

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

        model="gpt-4o",
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
    Write clear, detailed documentation in valid HTML to be inserted into a Jinja template. Output valid HTML without triple backticks, code fences, or extra symbols like >>>. Do not use any Markdown syntax (such as ** ** or __ __) for bold text; only use HTML <strong> tags for emphasis. Use headings (such as <h2> or <h3>) occasionally only on MAJOR new sections, but primarily use paragraphs (<p>) with inline styling. All text should default to a 'whitesmoke' color (for example, use style="color:whitesmoke;"). Bold all important terms and keywords by wrapping them in <strong> tags (for example, <strong>important term</strong>).

    For any actual code references or code snippets—identified by context or formatting—wrap them in a <code> tag styled with a cold tech blue color and a monospaced font (for example, <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;">exampleCode</code>).

    <strong>Enforce structure strictly:</strong> Use an <strong>ordered list (<ol>)</strong> whenever the content describes a clear step-by-step process, sequence of operations, or historical developments—<strong>always</strong>. If the text describes types, categories, examples, or grouped concepts without a required order, use an <strong>unordered list (<ul>)</strong> instead of paragraphs sparingly, only if clearly warranted. Do not collapse clearly structured sequences or groupings into plain text. If a process or grouping is implied but not explicitly stated as a list, <strong>still format it as a list</strong> if the structure is logically clear.

    Avoid excessive or unnecessary lists. Only use <ul> or <ol> when the content strongly implies grouping or order. Otherwise, favor paragraphs (<p>).

    At the end of each and every single element of HTML, insert '<!-- END_SECTION -->'.

    <strong>Subtle Contextual Insight Rule:</strong> When necessary, include <strong>short, direct context-building remarks</strong> to explain:
    1. <strong>Why a concept matters</strong> in the current topic.
    2. <strong>What role the concept plays</strong> in the overall subject area or system.
    3. <strong>How it connects to the previous content</strong>.

    These remarks must be integrated seamlessly, expressed in one or two sentences max, and <strong>strictly tied to the topic at hand</strong>—not general summaries or extrapolations. If no context is needed, skip it.

    <strong>Concept Clarity Rule (NEW):</strong> When a new concept, event, term, process, or component is introduced, <strong>briefly define what it is</strong> and <strong>explain how it fits into the subject matter or relates to earlier material</strong>. This should be concise and embedded naturally into the explanation, ensuring the learner can follow the logic and purpose of the term without needing outside references.

    <strong>Example Handling Rule:</strong> If the provided content includes an <strong>example, scenario, or source excerpt</strong> meant to illustrate a concept, <strong>always include it</strong> in the output. When an example is used, it may substitute for a longer explanation if the concept becomes clear through it. Prefer slightly more concise, conceptual phrasing in these cases—but only if the example fully supports the understanding.

    Do not introduce the output with framing or general statements. Do not address an audience or use phrases like 'you should' or 'we now see.' Stick strictly to factual, structured, and academic exposition.

    The following is a summary of previously covered material. Do not repeat this information, but use it to build continuity and contextual understanding if helpful:
    {previous_content}

    Now focus primarily and thoroughly on the following new content. Generate deeply detailed, structured documentation that closely adheres to the text, with structure and insight as described:
    {file_content}
    """
            },
        ],
        stream=True
    )

    global string_buffer
    for chunk in completion:
        try:
            delta = chunk.choices[0].delta
            content = delta.content if delta and hasattr(delta, "content") else None

            if content:
                string_buffer += content
                output_buffer += content
                socketio.emit("update_notes", {"notes": content})
                with open(current_file, "a", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                end_section(string_buffer)
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")

    socketio.emit("update_notes", {"notes" : "<br/><br/>"})

    output_buffer = strip_html(output_buffer)

    # Embed what gpt just created
    embedded_notes = embed_text(output_buffer)
    # Then, add the current_embedding to the CSV
    file_exists = os.path.isfile(FILE_EMBEDDINGS)   # Check if the CSV already exists

    # Append to the CSV
    with open(FILE_EMBEDDINGS, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["filename", "text", "embedding"])
        writer.writerow([os.path.basename(current_file), output_buffer, str(embedded_notes)])