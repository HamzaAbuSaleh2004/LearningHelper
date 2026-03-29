import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
import pickle
import os
from tqdm import tqdm

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'cleaned_courses.csv')
# Pointing to the NEW model folder
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'sbert_local')
EMBEDDINGS_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'course_embeddings.pkl')

# ---------------------------------------------------------
# THE SECRET SAUCE: MEAN POOLING
# This function averages all token vectors to get one sentence vector
# ---------------------------------------------------------
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def generate_embeddings():
    print("⏳ Loading SBERT Model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModel.from_pretrained(MODEL_PATH)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    # Load Data
    df = pd.read_csv(DATA_PATH)
    texts = df['text_for_bert'].tolist()
    
    embeddings_list = []
    print(f"🚀 Generating embeddings for {len(texts)} courses...")
    
    batch_size = 32
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i + batch_size]
        
        inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        # USE MEAN POOLING HERE
        sentence_embeddings = mean_pooling(outputs, inputs['attention_mask'])
        
        # Normalize embeddings (Important for Cosine Similarity!)
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        
        embeddings_list.extend(sentence_embeddings.cpu().numpy())

    with open(EMBEDDINGS_PATH, 'wb') as f:
        pickle.dump({'df': df, 'embeddings': embeddings_list}, f)
        
    print(f"✅ SBERT Embeddings saved to {EMBEDDINGS_PATH}")

if __name__ == "__main__":
    generate_embeddings()