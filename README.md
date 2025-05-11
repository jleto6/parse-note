
# ParseNote

ParseNote is an AI-powered learning tool that transforms large-scale, unstructured technical content—such as lecture transcripts or textbook excerpts—into semantically structured, high-quality documentation. The system uses large language models (LLMs), embedding-based similarity, and retrieval-augmented generation (RAG) to produce a distilled version of the content alongside a logically ordered outline. This distillation preserves core ideas while enhancing structure and clarity, forming the foundation for generating organized documentation and enabling intelligent retrieval through embeddings.

## How It Works

### 1. Large, Unstructured Input  
The system begins with raw, unordered files containing academic or technical material. These may include lecture dumps, notes, or instructional documents in their original, unedited form.

### 2. Semantic Outline Generation via GPT-4  
The raw input is sent to a language model that produces a high-level semantic outline:
- Topics are ordered from foundational to advanced.
- The outline acts as both a distilled version of the original content and a semantic guide for organizing the document.
- Output is stored as a serialized DataFrame for downstream use.

### 3. Sliding Window Embedding + Semantic Assignment  
To semantically align the unstructured input with the generated outline, the system applies a sliding window embedding strategy combined with cosine similarity scoring. This functions as a custom topic modeling system:
- Chunks of the input are embedded using OpenAI’s `text-embedding-3-small`.
- Each chunk is compared against precomputed embeddings of outline sections.
- Chunks are assigned to the section with the highest semantic similarity score.

This creates a meaning-based mapping of unordered content into semantically coherent sections without relying on its original sequence or formatting.

### 4. Section Embedding for Retrieval-Augmented Generation (RAG)  
Each outline section is embedded and stored to support semantic search and question answering. These embeddings enable high-accuracy chunk retrieval during inference or user interaction.

### 5. HTML Note Generation (Section-by-Section)  
Organized content sections are sent back to the LLM for structured note generation:
- Each section is rewritten as coherent, technical documentation.
- Output is formatted as valid HTML, ready for integration into Jinja templates or rendered directly via the web interface.
- All content maintains semantic fidelity to the original material while improving clarity and structure.

### 6. Document Chat with RAG-Based Retrieval  
A built-in chat interface enables users to query the document:
- The query is embedded and used to retrieve the most relevant section(s) based on similarity to the stored embeddings.
- The system includes the distilled document as part of the context.
- GPT-4 generates an answer using both the retrieved section and distilled document to ensure completeness and specificity.


## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/jleto6/parse-note.git](https://github.com/jleto6/parse-note.git)
    ```
2.  **Navigate to the directory:**
    ```bash
    cd parse-note
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up API keys:**
    ```bash
    export OPENAI_API_KEY=your_key_here
    ```
5.  **Run the application:**
    ```bash
    python app/main.py
    ```

A Flask server will start and open in your browser. Upload your raw content—this can include text files, lecture transcripts, PDFs, or images—and the system will automatically generate a semantic outline, organize the material, and return structured documentation ready for retrieval, analysis, or integration.

## Technologies Used

* **OpenAI GPT-4:** For outline generation and structured HTML note synthesis
* **OpenAI text-embedding-3-small:** For embedding and semantic similarity scoring
* **Flask + Flask-SocketIO:** For local web-based document processing and interaction
* **Pandas, NumPy:** For data handling, transformation, and CSV/PKL serialization
* **Prompt Engineering:** For controlling GPT output format and semantic consistency

## Planned Development

- Full-featured web interface with user logins, saved sessions, and workspace management  
- PDF and Markdown export of generated documentation  
- Human-in-the-loop feedback system for iterative refinement of generated documentation  