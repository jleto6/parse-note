from openai import OpenAI
import numpy as np
import os
import time

from config import COMPLETED_NOTES
from nlp.embedding_utils import similarity_score, get_embeddings_batch

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def line_sort(file_path, section_embeddings):

    assignments = {section: [] for section in section_embeddings}  # Create a dictionary to store which lines get assigned to which section

    # Read all the lines from the input file
    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Strip whitespace and remove any empty lines
    lines = [line.strip() for line in raw_lines if line.strip()]

    # Get embeddings for all cleaned lines in one batch API call
    line_embeddings = get_embeddings_batch(lines)

    for line, line_embedding in zip(lines, line_embeddings):
        # Find the best matching section + its score
        best_pair = max(
            section_embeddings.items(),
            key=lambda item: similarity_score(line_embedding, item[1])
        )

        best_section = best_pair[0]
        section_vector = best_pair[1]
        score = similarity_score(line_embedding, section_vector)

        # Optional: print out debug info
        # print(f"Line: {line[:60]}... → Best match: {best_section} (Score: {score:.4f})")

        assignments[best_section].append(line)

    # Save each section's grouped lines to its own file
    for best_section, grouped_lines in assignments.items():
        with open(f"{COMPLETED_NOTES}/{best_section}", "w", encoding="utf-8") as f:
            for line in grouped_lines:
                f.write(line + "\n")  # Write each line on its own line in the output file

    # Return the full assignment mapping for further use if needed
    return assignments

