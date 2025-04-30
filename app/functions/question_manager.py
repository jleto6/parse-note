import base64
from openai import OpenAI
import openai
import os
import markdown
from flask_socketio import SocketIO
import json
from functions.gpt_functions import end_answer, end_section

from config import ANSWERS

deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  ) # Use Deepseek
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

previous_content = ""
string_buffer = ""
answer_buffer = ""


# Text File to Store GPT Question Conversations 
open(ANSWERS, "w").close()  # Ensure the file exists by creating it if it doesnt

# QUESTION CALL
def question_call(question, selection):
    from app import socketio

    global previous_content
    # Read the content of the current file
    with open(content, "r") as file:
        file_content = file.read()
        previous_content += file_content # Store all read files in memory so GPT knows whats covered

    # Read the content of the covered material file
    with open(ANSWERS, "r") as file:
        answers_txt = file.read()

    # GPT Call
    completion = openai_client.responses.create(
    model="gpt-4o",
    input=[
        {"role": "system", "content": "You are an AI that generates answers to questions while maintaining continuity across sections when relevant. Prior responses should be considered only if they directly relate to the new question. If the new question is unrelated, answer independently without incorporating previous answers."},
        {"role": "user", "content": f"""
    Write clear, detailed notes in valid HTML to be inserted into a Jinja template. Output valid HTML without triple backticks, code fences, or extra symbols like >>>. Do not use any Markdown syntax (such as ** ** or __ __) for bold text; only use HTML <strong> tags. Primarily use paragraphs (<p>) with inline styling. All text should default to a 'whitesmoke' color (for example, use style="color:whitesmoke;") and size 14px font. Bold all important terms and words of interest by wrapping them in <strong> tags (for example, <strong>important term</strong>).

    For any actual code references or code snippets—identified by context or explicit formatting instructions—wrap them in a <code> tag styled with a cold tech blue color and a monospaced font (for example, <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;">exampleCode</code>).

    Use an ordered list (<ol>) whenever you detect a clear, step-by-step process or sequence of instructions. Otherwise, favor paragraphs (<p>). Unordered lists (<ul>) can be used sparingly for listing related items when no specific order is required. At the end of each and every single element of HTML, insert '<!-- END_SECTION -->'.

    Present facts directly without introductory framing, explanations of importance, or general overviews. Avoid addressing an audience or using terms like 'we,' 'you,' or 'must.' Use natural, straightforward language without formal phrasing. Stick closely to the provided content and clarify only when absolutely necessary; do not add extra explanations or extrapolate beyond the provided information.

    The following text is a **summary of previous sections** already covered. Do not repeat this information but ensure new notes remain consistent with what has been stated:
    {previous_content}

    Now, process the following question:{question} on the topic"{selection} and write an explenation while maintaining continuity with the previous sections.
    """},
    ],
    stream=True
)
    for chunk in completion:
        global answer_buffer
        # Handle different possible chunk formats
        try:
            content = None

            if isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, "content") and chunk.content:
                content = chunk.content
            elif hasattr(chunk, "delta"):
                delta = chunk.delta
                if isinstance(delta, str):
                    content = delta
                elif hasattr(delta, "content") and delta.content:
                    content = delta.content

            if content:
                socketio.emit("answers", {"answer": content})
                open(ANSWERS, "a").write(content)

                answer_buffer += content
                end_answer(answer_buffer) # Check if a section was completed

                yield content
        
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")
        
    socketio.emit("answers", {"answer" : "<br/><br/>"})

# EXPLAIN
def explanation(selection):
    from app.app import socketio

    content = openai_client.responses.create(
        model="gpt-4o",
        input = [
        {
            "role": "system",
            "content": (
                "You are an AI that improves the clarity and depth of existing HTML-based study notes. "
                "You do not introduce new topics or visual elements. Your task is to enhance the explanation "
                "within the provided HTML while preserving all tags, structure, and inline styling. "
                "If the formatting is minimal or inconsistent, infer the original structure and apply it cleanly. "
                "You are not a Markdown generator. You are an HTML generator. Never use Markdown syntax such as triple backticks, "
                "asterisks, or numbered lines outside HTML tags. If you see triple backticks or lines that start with '1.' "
                "and are not in proper HTML tags, delete them."
            )
        },
        {
            "role": "user",
            "content": f"""
    You will be given a snippet of HTML that was selected from an educational note-taking interface. Your job is to rewrite the explanation using clearer and more detailed language, **without changing the HTML structure**. Follow these formatting rules strictly:

    - Output valid HTML only — do not include backticks, code fences, or Markdown-style formatting.
    - Do **not** remove or add new HTML tags unless they are clearly missing and necessary to fix broken formatting.
    - All text should default to a 'whitesmoke' color using inline style and 14px font size (e.g., <p style="color:whitesmoke; font-size:14px;">).
    - Bold all important terms and notable keywords using <strong>.
    - For any actual code references or inline snippets, use:
    <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;">yourCode</code>
    - Use <ol> for clear step-by-step instructions; use <ul> only when listing unordered items. Lists should follow the same inline styling as paragraphs.
    - Ensure every <p>, <li>, or heading includes the inline style `style="color:whitesmoke; font-size:14px;"` unless already present. If the style is missing, add it.

    Do **not** add general overviews or summaries. Stick closely to the content provided in the HTML, improving the clarity and explanation of what is already there without expanding scope.

    **Important:** Do not use triple backticks, `1.` line prefixes, or any Markdown formatting. You are not outputting Markdown. Remove any existing Markdown if found. Your response must consist of only valid, styled HTML elements with no leading or trailing formatting blocks.

    The following is a complete paragraph or block of study notes. Expand upon this exact content by adding 1–2 sentences directly **after the final sentence**, staying within the same tone and level of formality. Do **not summarize** or restructure it. Just deepen the explanation slightly with relevant, directly related facts or clarifications.

    Here is the content to expand:
    {selection}
    """
        }
    ]
    )

    print(content.output_text)
    socketio.emit("explanation", {"explanation": content.output_text})
