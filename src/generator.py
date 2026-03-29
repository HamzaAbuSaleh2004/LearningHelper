import os
import json
from groq import Groq

# 1. Setup the Client
# Load key from environment or use a placeholder
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_API_KEY_HERE") 
client = Groq(api_key=GROQ_API_KEY)

def generate_personalized_roadmap(user_schedule, user_goal, course_list):
    """
    Uses Llama 3.3 to generate a visual roadmap (Mermaid) and a study schedule (JSON).
    """
    
    prompt = f"""
    You are an expert academic counselor.
    The student wants to learn: "{user_goal}".
    They have selected these courses: {course_list}.
    
    Their personal constraints/schedule: "{user_schedule}".
    
    Task:
    1. Create a step-by-step flowchart logic (Mermaid.js syntax) connecting these courses logically (Beginner -> Advanced).
    2. Create a 4-week study schedule tailored to their constraints.
    
    Output Format (STRICT JSON):
    {{
        "mermaid_syntax": "graph TD; NodeA[Topic A] --> NodeB[Topic B];",
        "study_schedule": [
            {{ "week": 1, "topic": "...", "tasks": ["Task 1", "Task 2"] }},
            {{ "week": 2, "topic": "...", "tasks": ["Task 3", "Task 4"] }}
        ]
    }}
    
    RULES:
    - Output ONLY valid JSON.
    - Do NOT wrap the output in markdown (no ```json or ```mermaid tags).
    - Do NOT use parentheses () or special characters inside the Mermaid node names (e.g. Node[Python (Advanced)] is BAD. Use Node[Python Advanced]).
    """

    try:
        # 3. Call the Llama 3.3 Model
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs only raw JSON. No markdown."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile", 
            temperature=0.1, # Very low temperature to force strict formatting
            response_format={"type": "json_object"}, 
        )

        # 4. Parse the result
        content = chat_completion.choices[0].message.content
        data = json.loads(content)
        
        # ---------------------------------------------------
        # 🛑 SAFETY CLEANING (Fixes the Syntax Error)
        # ---------------------------------------------------
        mermaid_code = data.get("mermaid_syntax", "")
        
        # Remove markdown tags if the AI disobeyed
        mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
        
        # Ensure it starts with graph TD
        if not mermaid_code.startswith("graph"):
            mermaid_code = "graph TD;\n" + mermaid_code
            
        # Update the data with the clean code
        data["mermaid_syntax"] = mermaid_code

        return data

    except Exception as e:
        print(f"Error generating roadmap: {e}")
        # Fallback chart in case of error
        return {
            "mermaid_syntax": "graph TD; Error[AI Failed to Load] --> Retry[Try Again];",
            "study_schedule": []
        }