from openai import OpenAI
client = OpenAI()
import csv
from app.config import RAW_TEXT, EMBEDDINGS

def get_embedding(text, model="text-embedding-3-small"):
    return client.embeddings.create(input=[text], model=model).data[0].embedding

def embed_corpus(corpus):
    # Read the content of the corpus
    with open(corpus, "r") as file:
        corpus = file.read()
    chunks = corpus.splitlines() # Split it line by line

    # Embed each line
    embeddings = [get_embedding(chunk) for chunk in chunks if chunk.strip()]

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
    
# embed_corpus(RAW_TEXT)

question = input("Enter your question: ")

question_embedding = get_embedding(question)

response = client.responses.create(
    model="gpt-3.5-turbo",
    input=[
        {
            "role": "developer",
            "content": "Anwer briefly."
        },
        {
            "role": "user",
            "content": question
        }
    ]
)
print(response.output_text)