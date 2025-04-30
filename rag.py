from openai import OpenAI
client = OpenAI()
import csv
import pandas as pd
import numpy as np
import ast
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

# GPT Question
question = input("Enter your question: ")
question_embedding = get_embedding(question)

# Load the saved CSV file as a pandas DataFrame
corpus_df = pd.read_csv(EMBEDDINGS)
corpus_df['embedding'] = corpus_df['embedding'].apply(ast.literal_eval) # Convert the embedding column from a string back into a list of floats

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

# Call GPT with new context
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            # "content": f"Use the following context to answer the question:\n\n{context}"
        },
        {
            "role": "user",
            "content": question
        }
    ]
)
print(response.choices[0].message.content)