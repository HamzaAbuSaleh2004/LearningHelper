import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'sbert_local')
EMBEDDINGS_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'course_embeddings.pkl')

class CourseRecommender:
    def __init__(self):
        # Load Data
        if not os.path.exists(EMBEDDINGS_PATH):
            raise FileNotFoundError("Embeddings not found. Run embeddings.py!")
        with open(EMBEDDINGS_PATH, 'rb') as f:
            data = pickle.load(f)
            self.df = data['df']
            self.course_embeddings = data['embeddings']
        
        # Load SBERT
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        self.model = AutoModel.from_pretrained(MODEL_PATH)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

    # Helper function for Mean Pooling
    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use Mean Pooling & Normalize
        embedding = self._mean_pooling(outputs, inputs['attention_mask'])
        embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
        
        return embedding.cpu().numpy()

    def recommend(self, user_query, user_level, top_n=20):
        enhanced_query = f"{user_query}" 
        user_vector = self.get_embedding(enhanced_query)

        similarities = cosine_similarity(user_vector, self.course_embeddings).flatten()
        results = self.df.copy()
        results['score'] = similarities
        
        # KEYWORD BOOST: If exact title exists in query (case-insensitive), give a massive boost
        # SBERT is great for synonyms, but precise titles matter to the user
        results['title_lower'] = results['course_title'].str.lower()
        query_lower = user_query.lower()
        results.loc[results['title_lower'].str.contains(query_lower, case=False, na=False), 'score'] += 0.4

        # THRESHOLD: Lowered to 0.20 to catch more "related" courses
        results = results[results['score'] > 0.20]

        if user_level != "All Levels":
            # Boost logic
            results.loc[results['level'] == user_level, 'score'] += 0.1

        # Clamp score to [0, 1] so the UI never shows >100% match
        results['score'] = results['score'].clip(upper=1.0)

        return results.sort_values(by='score', ascending=False).head(top_n)