import base64
from openai import OpenAI
import openai
import os
openai.api_key = os.getenv("OPENAI_API_KEY")


# -----------------------------------------------
# GPT Function
# -----------------------------------------------

# GPT Prompt
prompt = f"""
“Write clear and detailed notes in full sentences without bullet points. State facts directly with no introductory framing, explanations of importance, or general overviews. Do not use phrases like ‘the content revolves around’ or ‘this topic is crucial for understanding.’ Avoid addressing an audience—do not use words like ‘we,’ ‘you,’ or ‘must.’ Use natural, straightforward language without third-person narration or formal phrasing. Stick closely to the provided content, only explaining concepts slightly further if necessary for clarity. Do not expand beyond what is mentioned. Begin writing immediately with factual information. The notes should be highly detailed yet concise, eliminating redundancy while maintaining clarity. They should be ready to study as written, without needing reorganization or further editing.”        """
prompt1 = "Whats in this image?"

def text_call(content):
    # Read the content of the current file
    with open(content, "r") as file:
        file_content = file.read()
    # Read the content of the covered material file
    with open("notes.txt", "r") as file:
        previous_content = file.read()

    # GPT Call
    completion = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an AI that generates detailed notes while maintaining continuity across sections."},
        {"role": "user", "content": f"""
        Write clear and detailed notes in full sentences without bullet points. State facts directly with no introductory framing, explanations of importance, or general overviews. Do not use phrases like ‘the content revolves around’ or ‘this topic is crucial for understanding.’ Avoid addressing an audience—do not use words like ‘we,’ ‘you,’ or ‘must.’ Use natural, straightforward language without third-person narration or formal phrasing. Stick closely to the provided content, only explaining concepts slightly further if necessary for clarity. Do not expand beyond what is mentioned. Begin writing immediately with factual information.

        The following text is a **summary of previous sections** already covered. Do not repeat this information but ensure new notes remain consistent with what has been stated:
        {previous_content}

        Now, process the following new content and write detailed notes while maintaining continuity with the previous sections:
        {file_content}
        """}
    ]
)
    response_content = completion.choices[0].message.content     # Process GPT Response
    # Appends all text to a text file so GPT can reference already covered material
    with open("notes.txt", "a", encoding="utf-8") as file:
           file.write(response_content + "\n")  # Appends text to output file
    #print(f"NOTES: {response_content}")

def image_call(file_path):
    # Get the Base64 string of the file
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    base64_image = encode_image(file_path)

    # GPT Call
    completion = openai.chat.completions.create(
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

def question_call(question):
    from app import socketio

    # Read the content of the covered material file
    with open("answers.txt", "r") as file:
        answers_txt = file.read()

    # GPT Call
    completion = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are an AI that generates very brief conceptual answers to questions while maintaining continuity across sections when relevant. Prior responses should be considered only if they directly relate to the new question. If the new question is unrelated, answer independently without incorporating previous answers."},
        {"role": "user", "content": f"""
        Write a brief and conceptual explanation conversationally without bullet points. State facts directly with no introductory framing, explanations of importance, or general overviews. Avoid addressing an audience—do not use words like ‘we,’ ‘you,’ or ‘must.’ Use natural, straightforward language without third-person narration or formal phrasing. Stick closely to the provided content, only explaining concepts slightly further if necessary for clarity. Do not expand beyond what is mentioned. Begin writing immediately with factual information.

        The following text contains previous answers you have given. Use them only for maintaining consistency if relevant to the new question. If the new question is unrelated, ignore prior responses:
        {answers_txt}

        Now, process the following new question {question} on the topic {question} and write the answer/explanation
        """}
    ]
)
    response_content = completion.choices[0].message.content     # Process GPT Response
    # Appends all text to a text file so GPT can reference already covered material
    with open("answers.txt", "a", encoding="utf-8") as file:
           file.write(response_content + "\n")  # Appends text to output file

    # Emit the answers to socketio
    socketio.emit("answers", {"answer": f"{response_content} <br/><br/>"})

    return response_content



  