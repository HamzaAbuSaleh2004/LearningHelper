import sys
import os
import traceback

# Add src to path
SRC_DIR = os.path.join(os.getcwd(), "src")
sys.path.insert(0, SRC_DIR)

try:
    from recommender import CourseRecommender
    print("⏳ Attempting to initialize CourseRecommender...")
    engine = CourseRecommender()
    print("✅ Success!")
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
