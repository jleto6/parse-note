import base64
from openai import OpenAI
import openai
import os
import markdown

from flask_socketio import SocketIO
import json

# Use Deepseek
deepseek_client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1"  )

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check for section end function
string_buffer = ""
answer_buffer = ""
def end_section(string_buffer):
    from app import socketio
    if "<!-- END_SECTION -->" in string_buffer:
        string_buffer = markdown.markdown(string_buffer) # Convert to HTML
        socketio.emit("update_notes", {"notes": string_buffer, "refresh": True})

def end_answer(answer_buffer):
    from app import socketio
    if "<!-- END_SECTION -->" in answer_buffer:
        answer_buffer = markdown.markdown(answer_buffer) # Convert to HTML
        socketio.emit("answers", {"answer": answer_buffer, "refresh": True})

previous_content = ""

# -----------------------------------------------
# GPT Function
# -----------------------------------------------

# GPT Prompt
prompt = f""""
“Write clear and detailed notes in full sentences without bullet points. State facts directly with no introductory framing, explanations of importance, or general overviews. Do not use phrases like ‘the content revolves around’ or ‘this topic is crucial for understanding.’ Avoid addressing an audience—do not use words like ‘we,’ ‘you,’ or ‘must.’ Use natural, straightforward language without third-person narration or formal phrasing. Stick closely to the provided content, only explaining concepts slightly further if necessary for clarity. Do not expand beyond what is mentioned. Begin writing immediately with factual information. The notes should be highly detailed yet concise, eliminating redundancy while maintaining clarity. They should be ready to study as written, without needing reorganization or further editing.”        """
prompt1 = "Whats in this image?"

def notes_creation(content):
    from app import socketio

    global previous_content
    # Read the content of the current file
    with open(content, "r") as file:
        file_content = file.read()
        previous_content += file_content # Store all read files in memory so GPT knows whats covered

    # GPT Call
    completion = openai_client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an AI that generates extremely detailed, visually appealing, sentence-based notes while maintaining "
                    "continuity across sections. Do not introduce any information that goes beyond the scope of the provided content."
                )
            },
            {
                "role": "user",
                "content": f"""
    Write clear, detailed notes in valid HTML to be inserted into a Jinja template. Output valid HTML without triple backticks, code fences, or extra symbols like >>>. Do not use any Markdown syntax (such as ** ** or __ __) for bold text; only use HTML <strong> tags. Use headings (such as <h2> or <h3>) occasionally only on MAJOR new sections, but primarily use paragraphs (<p>) with inline styling. All text should default to a 'whitesmoke' color (for example, use style="color:whitesmoke;"). Bold all important terms and words of interest by wrapping them in <strong> tags (for example, <strong>important term</strong>).

    For any actual code references or code snippets—identified by context or explicit formatting instructions—wrap them in a <code> tag styled with a cold tech blue color and a monospaced font (for example, <code style="color:#00aaff; font-family: Menlo, Monaco, 'Courier New', monospace;">exampleCode</code>).

    <strong>Detect and enforce structure strictly:</strong> Use an <strong>ordered list (<ol>)</strong> whenever the content describes a clear step-by-step process, sequence of operations, or execution stages—<strong>always</strong>. If the text describes types, categories, examples, or grouped concepts without a required order, use an <strong>unordered list (<ul>)</strong> instead of paragraphs sparringly, only if truly seen fit. Do not collapse clearly structured sequences or groupings into plain text. If a process or grouping is implied but not explicitly stated as a list, <strong>still format it as a list</strong> if the structure is logically clear.

    Avoid excessive or unnecessary lists. Only use <ul> or <ol> when the content strongly implies grouping or order. Otherwise, favor paragraphs (<p>).

    At the end of each and every single element of HTML, insert '<!-- END_SECTION -->'.

    Present facts directly without introductory framing, explanations of importance, or general overviews. Avoid addressing an audience or using terms like 'we,' 'you,' or 'must.' Use natural, straightforward language without formal phrasing. Stick closely to the provided content and clarify only when absolutely necessary; do not add extra explanations or extrapolate beyond the provided information.

    The following text is a **summary of previous sections** already covered. Do not repeat this information but ensure new notes remain consistent with what has been stated:
    {previous_content}

    Now focus **primarily and thoroughly** on the following new content. Generate detailed notes that closely adhere to the text, without going beyond it:
    {file_content}
    """
            }
        ],
        stream=True
    )

    global string_buffer
    for chunk in completion:
        #print(chunk)
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

                string_buffer += content

                #print(content, end="", flush=True)  # Stream to terminal
                socketio.emit("update_notes", {"notes" : content})
                with open("notes.txt", "a", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()  # Ensures content is written immediately to the file
                
                end_section(string_buffer) # Check if a section was completed

        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")

    socketio.emit("update_notes", {"notes" : "<br/><br/>"})

def image_call(file_path):
    # Get the Base64 string of the file
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    base64_image = encode_image(file_path)

    # GPT Call
    completion = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt1,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ],
    )
    # Process GPT Response
    response_content = completion.choices[0].message.content
    return response_content

# Text File to Store GPT Question Conversations 
open("answers.txt", "w").close()  # Ensure the file exists by creating it if it doesnt

def question_call(question, selection):
    from app import socketio

    # Read the content of the covered material file
    with open("answers.txt", "r") as file:
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
                open("answers.txt", "a").write(content)

                answer_buffer += content
                end_answer(answer_buffer) # Check if a section was completed

                yield content
        
        except Exception as e:
            print(f"\nError processing chunk: {e}")
            print(f"Chunk type: {type(chunk)}")
            print(f"Chunk content: {chunk}")
        
    socketio.emit("answers", {"answer" : "<br/><br/>"})


def explanation(selection):
    from app import socketio

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



  