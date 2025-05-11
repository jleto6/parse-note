import base64
from openai import OpenAI
import openai
import os
import markdown
from flask_socketio import SocketIO
import json
import re
import csv
import pandas as pd
import numpy as np
import ast
import os

from config import ANSWERS, RAW_TEXT, EMBEDDINGS, DISTILLED_DOC
from nlp.gpt_utils import end_answer, end_answer
from nlp.embedding_utils import embed_corpus, get_embedding, similarity_score

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

string_buffer = ""
answer_buffer = ""
previous_content = ""

# Text File to Store GPT Question Conversations 
open(ANSWERS, "w").close()  # Ensure the file exists by creating it if it doesnt


embed_corpus(RAW_TEXT)

# GPT QUESTION CALL 
def question_call(question, selection):
    from app import socketio

    # Get The Distilled Doc
    with open(DISTILLED_DOC, 'r', encoding="utf-8") as f:
        distilled_doc = f.read()

    # RAG Embeddings
    corpus_df = pd.read_csv(EMBEDDINGS) # Load the saved CSV file as a pandas DataFrame
    corpus_df['embedding'] = corpus_df['embedding'].apply(ast.literal_eval) # Convert the embedding column from a string back into a list of floats

    question_embedding = get_embedding(question) # Embedd the given question

    # Compute similarity scores for each chunk
    corpus_df["score"] = corpus_df["embedding"].apply( # Create a new 'score' column for each chunk
        lambda chunk_embedding: similarity_score(chunk_embedding, question_embedding) # Get a similarity score for each
    )
    top_chunk = corpus_df.sort_values("score", ascending=False).head(2) # sort the DataFrame by similarity score in descending order
    # print(top_chunk)
    context = "\n".join(top_chunk["text"].tolist()) # Get a string of top_chunk(s) 

    # GPT Call
    global previous_content

    # print(f"Asking question: {question}\n context used: {context}")

    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages = [
            {
                "role": "system",
                "content": (
                    "You're a knowledgeable expert in a one-on-one conversation. Respond in a natural, ongoing tone—like you're continuing a discussion with someone asking thoughtful follow-ups. "
                    "Format your response as clean, valid HTML for a Jinja template: use <p style='color:whitesmoke; font-size:16px;'> for paragraphs, <strong> for emphasis, "
                    "<code style='color:#00aaff; font-family: Menlo, Monaco, Courier New, monospace;'> for inline code, <ol> for steps, and <ul> for unordered lists. "
                    "Do not include triple backticks or markdown formatting—only raw HTML. After every paragraph or list item, append '<!-- END_ANSWER -->'."
                )
            },
            {
                "role": "user",
                "content": f"""
    Here is the distilled version of the document you're answering a question on, likely use it:
    {distilled_doc}

    You’ve just said:
    {previous_content}

    Here is some context of the question, use it if its useful:
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
