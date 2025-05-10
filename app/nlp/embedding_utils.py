from openai import OpenAI
import os
import csv
import numpy as np
from config import EMBEDDINGS

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # Use OpenAI

# Get embedding
def get_embedding(text, model="text-embedding-3-small"):
    return openai_client.embeddings.create(input=[text], model=model).data[0].embedding

# Function to compare two vectors similarity
# def similarity_score(page_embedding, question_embedding):
#     return np.dot(page_embedding, question_embedding) # Return their dot product 

def similarity_score(page_embedding, question_embedding):
    dot = np.dot(page_embedding, question_embedding)
    norm_product = np.linalg.norm(page_embedding) * np.linalg.norm(question_embedding)
    return dot / norm_product

def get_embeddings_batch(texts, model="text-embedding-3-small"):
    if isinstance(texts, str):
        texts = [texts]  # Ensure it's a list
    response = openai_client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]

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

# Function To Embed text
def embed_text(content):
    # Generate embedding for the content
    response = openai_client.embeddings.create(
        input=[content],
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    return embedding


# Function to split text into ~300-word chunks
def chunk_text_by_words(text, words_per_chunk=300):
    words = text.split()
    chunks = [
        ' '.join(words[i:i + words_per_chunk])
        for i in range(0, len(words), words_per_chunk)
    ]
    return chunks

# Function To Embedd a Corpus
def embed_corpus(corpus):
    # Read and clean the corpus as one block of text
    with open(corpus, "r", encoding="utf-8") as file:
        full_text = file.read()

    # Create word-based chunks (~300 words each)
    chunks = chunk_text_by_words(full_text, words_per_chunk=300)

    batch_size = 10
    all_embeddings = []

    # Batch the requests
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        response = openai_client.embeddings.create(
            input=batch,
            model="text-embedding-3-small"
        )
        all_embeddings.extend([item.embedding for item in response.data])

    # Write to CSV
    with open(EMBEDDINGS, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "embedding"])
        for text, embedding in zip(chunks, all_embeddings):
            writer.writerow([text, str(embedding)])