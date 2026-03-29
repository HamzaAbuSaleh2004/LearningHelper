from flask import Flask, render_template, request, session, redirect, url_for
from recommender import CourseRecommender
from generator import generate_personalized_roadmap 
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_for_session" # Required for passing data between pages

# Load SBERT
try:
    print("⏳ Loading SBERT Model...")
    engine = CourseRecommender()
    print("✅ Model Loaded!")
except Exception as e:
    print(f"❌ Error: {e}")
    engine = None

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendations = []
    search_query = ""
    selected_level = "All Levels"

    if request.method == 'POST':
        search_query = request.form.get('search_query')
        selected_level = request.form.get('level')

        if engine and search_query:
            results = engine.recommend(search_query, selected_level)
            
            if not results.empty:
                recommendations = results.to_dict(orient='records')
                # Save goal to session for the AI later
                session['user_goal'] = search_query 
    
    return render_template(
        'index.html', 
        recommendations=recommendations,
        search_query=search_query,
        selected_level=selected_level
    )

# ROUTE 2: Handle Course Selection -> Show Schedule Form
@app.route('/personalize', methods=['POST'])
def personalize():
    # Get the list of courses the user checked
    selected_courses = request.form.getlist('selected_courses')
    session['selected_courses'] = selected_courses
    return render_template('personalize.html')

# ROUTE 3: Call Llama 3 -> Show Final Roadmap
@app.route('/generate', methods=['POST'])
def generate():
    user_schedule = request.form.get('user_schedule')
    courses = session.get('selected_courses', [])
    goal = session.get('user_goal', "Learning")
    
    # Call Llama 3 (This takes ~2-3 seconds)
    ai_data = generate_personalized_roadmap(user_schedule, goal, courses)
    
    return render_template('roadmap.html', ai_data=ai_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)