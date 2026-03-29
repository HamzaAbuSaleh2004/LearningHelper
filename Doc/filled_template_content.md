# Student Roadmap AI - Capstone Project Documentation

## Project Overview

**Student Roadmap AI** is an intelligent web application designed to assist students and lifelong learners in navigating the vast landscape of online education. By leveraging advanced Natural Language Processing (NLP) and Large Language Models (LLM), the system provides personalized course recommendations and structured learning roadmaps tailored to individual goals and schedules.

### Problem Statement
With the exponential growth of online learning platforms like Udemy, Coursera, and edX, students often face "choice paralysis." Identifying relevant courses that match specific skill levels and career goals is time-consuming. Furthermore, simply finding a course is not enough; learners struggle to organize multiple resources into a coherent study plan that fits their personal time constraints.

### Solution
Student Roadmap AI solves these challenges by:
1.  **Understanding Intent**: Using semantic search (Sentence-BERT) to understand the *meaning* behind a user's query, not just keyword matching.
2.  **Personalized Recommendations**: Suggesting courses that align with the user's specific topic of interest and difficulty level.
3.  **Structured Guidance**: Utilizing a powerful LLM (Llama 3.3 via Groq) to generate a visual dependency graph (roadmap) and a week-by-week study schedule based on the user's selected courses and available time.

---

## System Analysis

### Functional Requirements
-   **User Search**: Users must be able to search for topics (e.g., "Web Development", "Data Science") and filter by difficulty level (Beginner, Intermediate, Expert).
-   **Course Recommendation**: The system must return a list of relevant courses with high semantic similarity to the user's query.
-   **Course Selection**: Users must be able to select multiple courses from the recommendations to include in their roadmap.
-   **Constraint Input**: Users must be able to specify their time availability (e.g., "2 hours per day", "Weekends only").
-   **Roadmap Generation**: The system must verify the logical order of courses and generate a visual flowchart.
-   **Schedule Generation**: The system must produce a text-based study plan broken down by weeks or modules.

### Non-Functional Requirements
-   **Performance**: Recommendation search should take less than 1 second. Roadmap generation should take less than 10 seconds.
-   **Usability**: The interface should be intuitive, with clear steps (Search -> Select -> Personalize -> View Roadmap).
-   **Accuracy**: Recommendations must be contextually relevant, not just random keyword matches.

---

## System Design

### Architecture
The application follows a standard Model-View-Controller (MVC) pattern adapted for a Flask web application.

-   **Frontend (View)**: HTML5, CSS3, JavaScript. Uses Jinja2 templating for dynamic content rendering.
-   **Backend (Controller)**: Python with Flask. Handles routing, session management, and API coordination.
-   **AI Engine (Model)**:
    -   **Local Model**: Sentence-BERT (`sentence-transformers/all-MiniLM-L6-v2`) for embedding generation and similarity search.
    -   **Cloud Model**: Llama 3.3-70b (via Groq API) for reasoning and content generation.

### Data Flow
1.  **Data Ingestion**: Raw course data (CSV) is cleaned and preprocessed. Title, level, and subject are combined into a rich text field.
2.  **Embedding Generation**: The rich text field is passed through SBERT to create high-dimensional vector embeddings, which are saved locally (`course_embeddings.pkl`).
3.  **User Query**: When a user searches, their query is embedded using the same SBERT model.
4.  **Similarity Search**: Cosine similarity is calculated between the query vector and all course vectors. Top results are returned.
5.  **Roadmap Generation**: Selected courses + User Goal + User Schedule are sent as a prompt to the Groq API. The LLM returns a JSON object containing Mermaid.js syntax for the chart and a JSON study schedule.

### Algorithm: Semantic Search
Instead of simple keyword matching, we use **Cosine Similarity** on vector embeddings.
$$ \text{similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|} $$
Where $A$ is the user query vector and $B$ is the course vector.

---

## Implementation Details

### Technology Stack
-   **Language**: Python 3.9+
-   **Web Framework**: Flask
-   **ML Libraries**: `torch`, `transformers`, `scikit-learn`, `pandas`
-   **API Provider**: Groq (for fast inference of Llama 3 models)
-   **Frontend**: HTML, custom CSS, Mermaid.js (for visualization)

### Key Code Components

#### 1. Data Preprocessing (`src/preprocessing.py`)
This script loads the raw dataset, removes duplicates, and creates a "text_for_bert" column that combines critical metadata for better embedding context.

```python
# Combining features for richer embeddings
df['text_for_bert'] = (
    df['course_title'] + 
    " (Level: " + df['level'] + 
    ", Subject: " + df['subject'] + ")"
)
```

#### 2. Recommender Engine (`src/recommender.py`)
This class manages the SBERT model. It loads the pre-computed embeddings and performs the real-time search.

```python
def recommend(self, user_query, user_level, top_n=5):
    # Convert user query to vector
    user_vector = self.get_embedding(user_query)
    
    # Calculate similarity
    similarities = cosine_similarity(user_vector, self.course_embeddings).flatten()
    
    # Filter and Sort
    results = self.df.copy()
    results['score'] = similarities
    return results.sort_values(by='score', ascending=False).head(top_n)
```

#### 3. Roadmap Generator (`src/generator.py`)
This module interfaces with the LLM to generate the structured plan. It instructs the model to output strict JSON to ensure the frontend can render it correctly.

```python
prompt = f"""
    You are an expert academic counselor.
    The student wants to learn: "{user_goal}".
    They have selected these courses: {course_list}.
    Their personal constraints/schedule: "{user_schedule}".
    
    Task:
    1. Create a step-by-step flowchart logic (Mermaid.js syntax).
    2. Create a 4-week study schedule.
    
    Output Format (STRICT JSON)...
"""
```

---

## Conclusion
The Student Roadmap AI successfully demonstrates how modern AI techniques can personalize education. By combining the speed and specificity of local embedding models with the reasoning capabilities of large language models, we provide users with actionable, tailored learning paths that adapt to their unique constraints.
