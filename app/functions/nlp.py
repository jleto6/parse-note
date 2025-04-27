from bertopic import BERTopic
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import numpy as np
import nltk
import os
import shutil
import re
from nltk.tokenize import sent_tokenize
import warnings

from config import TOPIC_OUTPUTS_DIR, RAW_TEXT

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

nltk.download('punkt', quiet=True)

def nlp():
    # ================================================
    # Load and Split Text
    # ================================================
    with open(RAW_TEXT, "r", encoding="utf-8") as f:
        text = f.read()

    char_count = len(text)
    # print(f"Character count: {char_count}")

    # Split text into small chunks
    words = text.split()
    chunk_size = 50  # adjust this to control how fine each doc is
    docs = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

    # print(f"Total docs after chunking: {len(docs)}")

    # ================================================
    # Create and Fit BERTopic with KMeans
    # ================================================
    n_clusters = max(2, len(docs) // 8)  # Topic groups to create per documents
    # print(f"Target number of clusters: {n_clusters}")

    kmeans_model = KMeans(n_clusters=n_clusters)

    topic_model = BERTopic(
        embedding_model="all-MiniLM-L6-v2",
        hdbscan_model=kmeans_model,
        umap_model=None
    )

    topics, probs = topic_model.fit_transform(docs)

    # ================================================
    # Save Output by Topic
    # ================================================
    topic_info = topic_model.get_topic_info()
    print(topic_info)

    if os.path.exists(TOPIC_OUTPUTS_DIR):
        shutil.rmtree(TOPIC_OUTPUTS_DIR)
    os.makedirs(TOPIC_OUTPUTS_DIR, exist_ok=True)

    # Clean topic names and map them to topic IDs
    topic_names = {}
    for _, row in topic_info.iterrows():
        topic_id = row["Topic"]
        topic_name_raw = row["Name"]
        # Remove leading numbers and underscores from the topic name
        topic_name_clean = re.sub(r'^\d+\s*[_-]*', '', topic_name_raw)
        topic_names[topic_id] = topic_name_clean

    # Save documents to files named with clean topic names
    for topic_id in set(topics):
        if topic_id == -1:
            print("Skipping outlier topic -1")
            continue

        topic_docs = [doc for i, doc in enumerate(docs) if topics[i] == topic_id]
        topic_name = topic_names.get(topic_id, f"topic_{topic_id}")
        safe_name = topic_name.replace(" ", "_").replace("/", "_")[:50]
        filename = f"{TOPIC_OUTPUTS_DIR}/{safe_name}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(topic_docs))

        print(f"Saved {len(topic_docs)} documents to topic {topic_id}: {filename}")