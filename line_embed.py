from openai import OpenAI
import numpy as np
import os
import time

from outline import create_outline

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_embedding(text):
    return client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    ).data[0].embedding

def line_sort(file_path, section_embeddings):
    assignments = {section: [] for section in section_embeddings}

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue  # skip empty lines


        line_embedding = get_embedding(line)
        # Find the section whose embedding is most similar to the line's embedding
        # max() returns the (section_name, embedding) pair with the highest similarity
        best_pair = max( # Get full (section_name, embedding) pair
            section_embeddings.items(),
            key=lambda item: cosine_similarity(line_embedding, item[1])
        )

        # Then extract the name and vector
        best_section = best_pair[0]
        section_vector = best_pair[1]

        score = cosine_similarity(line_embedding, section_vector) # Just get the score of the most best section

        print(f"Most Similar: {best_section}, with score: {score}")

        assignments[best_section].append(line) # Assign the line to that section in the grouping

        # Save each section's lines to its own file
        os.makedirs("output_sections", exist_ok=True)
        for section_name, lines in assignments.items():
            with open(f"output_sections/{section_name}.txt", "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line.strip() + "\n")

    return assignments

outline_df = create_outline("raw_text.txt")

section_embeddings = {
    row["filename"]: row["embedding"]
    for _, row in outline_df.iterrows()
}

line_sort("raw_text.txt", section_embeddings)

