import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import pickle
import os
import json
from tqdm import tqdm

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data source is the latest JSON cache from the course_rec app
CACHE_PATH = os.path.join(BASE_DIR, 'course_rec', 'courses_cache.json')
# Model path (assuming it exists in the same place)
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'sbert_local')
# Output path for the AI search index
EMBEDDINGS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'course_embeddings.pkl')

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def refresh_ai_index():
    print("⏳ Loading SBERT Model...")
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model not found at {MODEL_PATH}")
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModel.from_pretrained(MODEL_PATH)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    # Load Data from JSON
    print(f"📂 Loading courses from {CACHE_PATH}...")
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    
    # Create a DataFrame to keep structure consistent with recommender.py
    df = pd.DataFrame(courses)
    
    # Clean/Rename columns if necessary to match what recommender expect
    # Standard format: id, title, category, level, platform, etc.
    if 'title' in df.columns and 'course_title' not in df.columns:
        df['course_title'] = df['title']
    
    # Create the text for BERT (Title + Category + Level)
    texts = []
    for _, row in df.iterrows():
        text = f"{row.get('course_title', '')} (Category: {row.get('category', '')}, Level: {row.get('level', '')})"
        texts.append(text)
    
    embeddings_list = []
    print(f"🚀 Generating AI embeddings for {len(texts)} courses. This ensures all courses are searchable...")
    
    batch_size = 32
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i + batch_size]
        
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        sentence_embeddings = mean_pooling(outputs, inputs['attention_mask'])
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        
        embeddings_list.extend(sentence_embeddings.cpu().numpy())

    # Ensure target directory exists
    os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
    
    with open(EMBEDDINGS_PATH, 'wb') as f:
        pickle.dump({'df': df, 'embeddings': list(embeddings_list)}, f)
        
    print(f"✅ AI Search Index updated! Saved to {EMBEDDINGS_PATH}")

if __name__ == "__main__":
    refresh_ai_index()
