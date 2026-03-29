import os
from transformers import AutoTokenizer, AutoModel

# NEW MODEL: SBERT (Faster, Lighter, and Much Smarter for Search)
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Saving to a new folder 'sbert_local' to avoid confusion
SAVE_PATH = os.path.join(BASE_DIR, '..', 'models', 'sbert_local')

def download_and_save():
    print(f"🚀 Starting download for: {MODEL_NAME}")
    
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    print("Downloading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.save_pretrained(SAVE_PATH)

    print("Downloading Model...")
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.save_pretrained(SAVE_PATH)

    print(f"✅ Success! SBERT saved to {SAVE_PATH}")

if __name__ == "__main__":
    download_and_save()