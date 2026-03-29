# Student Roadmap AI - Comprehensive Project Analysis

This document provides a detailed breakdown of the "Student Roadmap AI" project. It covers the overall workflow, the tools and technologies used, and a deep-dive analysis of every source code file in the repository.

## 1. Project Overview & Workflow

**Project Name:** Student Roadmap AI
**Goal:** To help students find relevant courses based on their interests and level, and then generate a personalized study roadmap and schedule using a Large Language Model (LLM).

### The User Journey (Workflow)

1.  **Search & Discovery (`index.html` → `app.py` → `recommender.py`)**:
    *   The user visits the home page and enters a search query (e.g., "Python for Data Science") and selects a difficulty level.
    *   The backend uses **SBERT (Sentence-BERT)** to convert the user's query into a mathematical vector (embedding).
    *   It calculates the **Cosine Similarity** between the user's query vector and the pre-computed vectors of thousands of Udemy courses.
    *   The system filters out low-relevance matches (`score > 0.35`) and boosts courses matching the selected difficulty level.
    *   The top 5 most relevant courses are displayed to the user.

2.  **Selection & Constraint Input (`index.html` → `personalize.html`)**:
    *   The user reviews the recommended courses and selects the ones they want to take (via checkboxes).
    *   The user is taken to a "Personalize" page where they describe their schedule constraints (e.g., "I work 9-5, can study 2 hours a night").

3.  **Roadmap Generation (`personalize.html` → `app.py` → `generator.py` → `roadmap.html`)**:
    *   The system takes the *selected courses*, *user goal*, and *schedule constraints* and bundles them into a prompt.
    *   This prompt is sent to **Llama 3.3 (via Groq API)**.
    *   The LLM generates:
        *   **Mermaid.js Syntax**: A visual flowchart code string connecting the courses logically.
        *   **JSON Schedule**: A structured 4-week study plan detailing weekly topics and tasks.
    *   The final roadmap page renders the flowchart (using Mermaid.js) and displays the interactive weekly checklist.

---

## 2. Tools & Technologies

*   **Language:** Python 3.x
*   **Web Framework:** **Flask** (Lightweight web server to handle routes and templating).
*   **AI Models:**
    *   **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (SBERT). High-speed, high-quality sentence embeddings for semantic search.
    *   **LLM:** `llama-3.3-70b-versatile` (via **Groq**). Used for "thinking" tasks—generating the logic for the roadmap and schedule.
*   **Data Processing:**
    *   **Pandas:** For loading and manipulating the course CSV data.
    *   **Torch (PyTorch):** The backend machine learning engine for running SBERT.
    *   **Scikit-learn:** Used for `cosine_similarity` to find the "distance" between meanings.
    *   **Pickle:** For serializing (saving) the heavy embedding data so the app loads instantly.
*   **Frontend:**
    *   **Bootstrap 5:** For responsive, clean UI components.
    *   **Mermaid.js:** Javascript library for rendering flowcharts from text definitions.
    *   **FontAwesome:** For icons.

---

## 3. Detailed File Analysis

### A. Root Directory

#### 1. `main.py`
*   **Purpose:** Simple entry point script.
*   **Logic:** Contains a basic `main()` function that prints "Welcome..." and executes. It seems to be a placeholder or a test runner, as the real web app starts from `src/app.py`.

#### 2. `requirements.txt`
*   **Purpose:** Dependency management.
*   **Contents:** Lists critical libraries: `torch`, `transformers`, `pandas`, `numpy`, `scikit-learn`, `tqdm`, and `flask`.

---

### B. `src/` Directory (Core Logic)

#### 3. `src/config.py`
*   **Purpose:** Central configuration hub.
*   **Key Variables:**
    *   Defines absolute paths (`BASE_DIR`, `DATA_PATH`, `MODEL_PATH`) to ensure the code runs correctly regardless of where the script is executed.
    *   Points the model path to `models/bert_local`, though other files seem to reference `sbert_local`.

#### 4. `src/download_model.py`
*   **Purpose:** One-time setup script to download the AI model.
*   **Logic:**
    *   Specifies `MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'`.
    *   Uses `AutoTokenizer` and `AutoModel` from `transformers` to download the model files from HuggingFace.
    *   Saves them locally to `../models/sbert_local`. This is crucial so the app can run offline or without re-downloading 1GB+ of data every restart.

#### 5. `src/preprocessing.py`
*   **Purpose:** Data cleaning and feature engineering.
*   **Logic:**
    *   **`clean_data()`**:
        *   Loads raw data from `data/raw/udemy_courses.csv`.
        *   Drops duplicates.
        *   **Feature Engineering:** Creates a `text_for_bert` column. It intelligently concatenates `course_title`, `level`, and `subject` into a single string. This gives the AI more context (e.g., "Python (Level: Beginner, Subject: Web Dev)") than just the title alone.
        *   Saves the cleaned CSV to `data/processed/cleaned_courses.csv`.

#### 6. `src/embeddings.py`
*   **Purpose:** The heavy-lifting script that "reads" all courses and converts them to numbers (vectors).
*   **Logic:**
    *   Loads the cleaned CSV and the local SBERT model.
    *   **`mean_pooling()`**: A critical technical function. The model outputs vectors for every *token* (word part). Mean pooling averages them to get a single vector representing the *entire sentence*.
    *   **`generate_embeddings()`**:
        *   Iterates through courses in batches (size 32) using a GPU (if available) or CPU.
        *    Computes embeddings and **Normalizes** them (crucial for Cosine Similarity to work as a generic similarity metric).
        *   Saves the final result (DataFrame + Embeddings Matrix) to a pickle file `course_embeddings.pkl`.

#### 7. `src/recommender.py`
*   **Purpose:** The search engine class.
*   **Class `CourseRecommender`**:
    *   **`__init__`**: Loads the large pickle file and the SBERT model into RAM on startup.
    *   **`get_embedding(text)`**: Converts a single input string (user query) into a vector using the same Mean Pooling + Normalization logic as `embeddings.py`.
    *   **`recommend(user_query, user_level)`**:
        *   Embeds the `user_query`.
        *   Calculates `cosine_similarity` between the user query and *all* course embeddings.
        *   **Filtering:** Filters courses with a similarity score < 0.35 (noise reduction).
        *   **Boosting:** Adds a `+0.1` bonus score to courses that match the user's selected difficulty level (`user_level`), ensuring beginners get beginner courses even if an expert course has similar keywords.
        *   Returns the top 5 results.

#### 8. `src/generator.py`
*   **Purpose:** The "Brain" of the personalized roadmap. Interfaces with the Groq API (Llama 3).
*   **Logic:**
    *   **`generate_personalized_roadmap(user_schedule, user_goal, course_list)`**:
        *   Constructs a detailed prompt injecting the user's specific courses and schedule.
        *   Asks the LLM to output **Strict JSON**.
        *   **Safety Cleaning:** Includes a `try-except` block and string manipulation to clean up the LLM's output (e.g., stripping markdown backticks ` ```json `) to prevent JSON parsing crashes.
        *   Ensures the Mermaid syntax starts with `graph TD;`.
        *   Returns a dictionary with `mermaid_syntax` and `study_schedule`.

#### 9. `src/app.py`
*   **Purpose:** The Web Server Controller.
*   **Routes:**
    *   **`@app.route('/', ...)` (Index)**: Handles search. Accepts POST requests with a query, calls `recommender.recommend()`, and renders `index.html` with results.
    *   **`@app.route('/personalize', ...)`**: Receives the form submission of *checked* courses from the home page. Saves them to a temporary user `session` and renders `personalize.html`.
    *   **`@app.route('/generate', ...)`**: The final step. Takes constraints from `personalize.html`, retrieves courses from `session`, calls `generator.generate_personalized_roadmap()`, and renders the result on `roadmap.html`.

---

### C. Templates (`src/templates/`)

#### 10. `index.html`
*   **UI:** Modern Hero section with a gradient background.
*   **Components:**
    *   Search bar with a dropdown for "Level".
    *   **Results Loop:** Iterates through `recommendations` and creates a card for each course.
    *   **Match Badge:** Displays the AI match percentage (e.g., "85% Match").
    *   **Selection:** Wraps the cards in a `<form>` with checkboxes so users can select multiple courses.

#### 11. `personalize.html`
*   **UI:** A simple, focused form card.
*   **Function:**
    *   `textarea` for the user to input their schedule/constraints.
    *   "Magic" button (`btn-magic`) to trigger the generation process.
    *   Includes a Loading Overlay (`#loading-overlay`) because the LLM generation takes a few seconds.

#### 12. `roadmap.html`
*   **UI:** The final dashboard.
*   **Components:**
    *   **Mermaid Chart:** Uses `{{ ai_data.mermaid_syntax | safe }}` to inject the diagram code, which the `mermaid.esm.min.mjs` script renders into a visual graph.
    *   **Weekly Plan:** Loops through the JSON `study_schedule` to create a week-by-week checklist. Each task has a checkbox for the user to mark "done".

---

### D. Notebooks

#### 13. `notebooks/experimentation.ipynb`
*   **Analysis:** An empty Jupyter notebook (78 bytes). Likely created fo testing snippets or prototyping code before moving it to `.py` files, but currently unused.
