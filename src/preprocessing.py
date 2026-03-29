import pandas as pd
import os

# Define paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, '..', 'data', 'raw', 'udemy_courses.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, '..', 'data', 'processed', 'cleaned_courses.csv')

def clean_data():
    # 1. Load the data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"Dataset Loaded: {df.shape[0]} courses found.")

    # 2. Basic Cleaning
    # Drop duplicates just in case
    df = df.drop_duplicates(subset=['course_title'])
    
    # 3. Create a "Rich Text" column for BERT
    # Instead of just embedding the title, we combine Title + Level + Subject
    # Example: "Python for Beginners (Level: Beginner, Subject: Web Development)"
    df['text_for_bert'] = (
        df['course_title'] + 
        " (Level: " + df['level'] + 
        ", Subject: " + df['subject'] + ")"
    )

    # 4. Save the processed data
    output_dir = os.path.dirname(OUTPUT_FILE)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Cleaned data saved to: {OUTPUT_FILE}")
    print(df[['course_title', 'text_for_bert']].head(3))

if __name__ == "__main__":
    clean_data()