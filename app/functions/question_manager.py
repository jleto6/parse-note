import base64
from openai import OpenAI
import openai
import os
import markdown
from flask_socketio import SocketIO
import json
import re
from functions.gpt_functions import end_answer, end_answer

import csv
import pandas as pd
import numpy as np
import ast
import os

from config import ANSWERS, RAW_TEXT, EMBEDDINGS

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

def get_embedding(text, model="text-embedding-3-small"):
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding

# Function To Embedd a Corpus
def embed_corpus(corpus):
    # Read the content of the corpus
    with open(corpus, "r") as file:
        corpus = file.read()
    chunks = corpus.splitlines() # Split it line by line

    embeddings = [get_embedding(chunk) for chunk in chunks if chunk.strip()]     # Embed each line

    # Pair chunk with its respective embedding
    pairs = zip(chunks, embeddings)
    pairs = list(pairs)

    # Write to CSV file
    with open(EMBEDDINGS, "w", newline='') as f: # Open CSV file for writing
        writer = csv.writer(f) # Create a CSV writer object
        writer.writerow(["text", "embedding"]) # Write the header row
        # For text and embedding in pairs, write them to the CSV file
        for text, embedding in pairs:
            if text.strip(): # Only write non-empty text
                writer.writerow([text, str(embedding)])


string_buffer = ""
answer_buffer = ""
previous_content = ""

# Text File to Store GPT Question Conversations 
open(ANSWERS, "w").close()  # Ensure the file exists by creating it if it doesnt

# GPT QUESTION CALL 
def question_call(question, selection):
    from app import socketio

    # RAG

    # Load the saved CSV file as a pandas DataFrame
    corpus_df = pd.read_csv(EMBEDDINGS)
    corpus_df['embedding'] = corpus_df['embedding'].apply(ast.literal_eval) # Convert the embedding column from a string back into a list of floats

    question_embedding = get_embedding(question) # Embedd the given question

    # Function to compare two vectors similarity
    def similarity_score(page_embedding, question_embedding):
        return np.dot(page_embedding, question_embedding) # Return their dot product (similarity score)

    # Compute similarity scores for each chunk
    corpus_df["score"] = corpus_df["embedding"].apply( # Create a new 'score' column for each chunk
        lambda chunk_embedding: similarity_score(chunk_embedding, question_embedding) # Get a similarity score for each
    )
    top_chunk = corpus_df.sort_values("score", ascending=False).head(2) # sort the DataFrame by similarity score in descending order
    # print(top_chunk)
    context = "\n".join(top_chunk["text"].tolist()) # Get a string of top_chunk(s) 



    # GPT Call
    global previous_content

    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {
                "role": "system",
                "content": (
                    "You're a knowledgeable expert in a one-on-one conversation. Respond in a natural, ongoing tone—like you're continuing a discussion with someone asking thoughtful follow-ups. "
                    "Format your response as clean, valid HTML for a Jinja template: use <p style='color:whitesmoke; font-size:16px;'> for paragraphs, <strong> for emphasis, "
                    "<code style='color:#00aaff; font-family: Menlo, Monaco, Courier New, monospace;'> for inline code, <ol> for steps, and <ul> for unordered lists. "
                    "After every paragraph or list item, append '<!-- END_ANSWER -->'."
                )
            },
            {
                "role": "user",
                "content": f"""
    You’ve just said:
    {previous_content}

    Here is context to go off of for the question:
    {context}

    Now, here’s the question:
    {question}
    """
            }
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
                socketio.emit("answers", {"answer": content})
                with open(ANSWERS, "a", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                end_answer(string_buffer)
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")
        
    socketio.emit("answers", {"answer" : "<br/><br/>"})

    previous_content = re.sub(r"<.*?>", "", string_buffer)
