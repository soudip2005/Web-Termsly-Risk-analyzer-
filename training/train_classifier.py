import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# Define file paths
DATA_FILE = os.path.join(os.path.dirname(__file__), 'policies_dataset.csv')
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_classifier.joblib')

def train():
    print("Starting training...")
    
    # Create models directory if it doesn't exist
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    # 1. Load Data
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {DATA_FILE}")
        print("Please create 'policies_dataset.csv' with 'text' and 'risk' columns.")
        return

    # Handle missing data
    df.dropna(subset=['text', 'risk'], inplace=True)

    if df.empty:
        print("Dataset is empty or has no valid data. Aborting training.")
        return

    X = df['text']
    y = df['risk'] # Labels: 'safe', 'medium', 'high'

    # 2. Create a model pipeline
    # We will convert text to numbers (TF-IDF) and then classify
    vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)
    classifier = LogisticRegression(solver='lbfgs', max_iter=1000)# Good for small datasets

    # 3. Train the models
    print(f"Training on {len(X)} samples...")
    # First, train the vectorizer
    X_tfidf = vectorizer.fit_transform(X)
    
    # Then, train the classifier
    classifier.fit(X_tfidf, y)

    # 4. Save the models
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(classifier, MODEL_PATH)
    
    print(f"Training complete. Models saved to {MODEL_DIR}")

if __name__ == "__main__":
    train()