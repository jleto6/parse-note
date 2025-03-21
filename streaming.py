from openai import OpenAI
import os
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stream = openai_client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": "Say 'double bubble bath' ten times fast.",
        },
    ],
    stream=True,
)

for chunk in stream:
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
            print(content, end="", flush=True)

    except Exception as e:
        print(f"\nError processing chunk: {e}")
        print(f"Chunk type: {type(chunk)}")
        print(f"Chunk content: {chunk}")