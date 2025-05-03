import os

# Get the absolute path to this file (config.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the project root
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Now build DATA_DIR off of the project root
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

TOPIC_OUTPUTS_DIR = os.path.join(DATA_DIR, 'topic_outputs')
NOTE_INPUTS_DIR = os.path.join(DATA_DIR, 'note_inputs')

RAW_TEXT = os.path.join(DATA_DIR, 'raw_text.txt')
COMPLETED_NOTES_INDEX = os.path.join(DATA_DIR, 'completed_notes') # add .txt manually
COMPLETED_NOTES = os.path.join(DATA_DIR, 'completed_notes.txt')

ANSWERS = os.path.join(DATA_DIR, 'answers.txt')
EMBEDDINGS = os.path.join(DATA_DIR, 'embeddings.csv') # entire embdeded doc

FILE_EMBEDDINGS = os.path.join(DATA_DIR, 'file_embeddings.csv') # iterative embedding pipeline

