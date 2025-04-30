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

string_buffer = ""
answer_buffer = ""
previous_content = ""

# Text File to Store GPT Question Conversations 
open(ANSWERS, "w").close()  # Ensure the file exists by creating it if it doesnt

# QUESTION CALL 
def question_call(question, selection):
    from app import socketio

    global previous_content
    # # Read the content of the current file
    # with open(RAW_TEXT, "r") as file:
    #     file_content = file.read()
    #     previous_content += file_content # Store all read files in memory so GPT knows whats covered

    # Read the content of the covered material file
    # with open(ANSWERS, "r") as file:
    #     answers_txt = file.read()

    # GPT Call
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
