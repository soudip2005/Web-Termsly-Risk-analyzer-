import joblib
import os
import re

# Define file paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')
MODEL_PATH = os.path.join(MODEL_DIR, 'risk_classifier.joblib')

# Load the models once when the app starts
try:
    vectorizer = joblib.load(VECTORIZER_PATH)
    classifier = joblib.load(MODEL_PATH)
    MODELS_LOADED = True
except FileNotFoundError:
    print("Error: Models not found. Please run 'training/train_classifier.py' first.")
    MODELS_LOADED = False

# We can keep these as a fallback
RISK_KEYWORDS = {
    'high': ['sell your data', 'share with advertisers', 'no control', 'waive your rights', 'tracking', 'no deletion'],
    'medium': ['third-party', 'cookies', 'analytics', 'improve service', 'may share', 'store data']
}

def analyze_risk(full_text):
    """
    Analyzes the full text to classify risk and find risky sentences.
    """
    if not MODELS_LOADED:
        return "Error", ["Models are not loaded. Please train the model first."]

    # 1. Overall Risk Classification
    # Split text into sentences for classification
    # This regex is better at handling sentences.
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', full_text)
    
    # Filter out any tiny "sentences"
    sentences = [s.strip() for s in sentences if len(s.split()) > 5]

    if not sentences:
        return "Unknown", ["Could not find any analyzable sentences in the text."]

    # Get predictions for each sentence
    predictions = classifier.predict(vectorizer.transform(sentences))
    
    # Determine overall risk
    overall_risk = "Safe" # Start with safe
    if 'medium' in predictions:
        overall_risk = 'Medium Risk'
    if 'high' in predictions:
        overall_risk = 'High Risk'
        
    # 2. Highlight Important Clauses
    highlights = []
    for sentence, prediction in zip(sentences, predictions):
        # Only keep sentences that are a reasonable length
        if len(sentence.split()) > 100: # Skip very long sentences
            continue

        if prediction == 'high':
            highlights.append(f"[HIGH RISK] {sentence}")
        elif prediction == 'medium':
            highlights.append(f"[MEDIUM RISK] {sentence}")

    # Fallback: If model found no risks but text is long, use keywords
    if not highlights and len(sentences) > 10:
        for sentence in sentences:
            lower_sentence = sentence.lower()
            if any(kw in lower_sentence for kw in RISK_KEYWORDS['high']):
                highlights.append(f"[HIGH RISK] {sentence}")
            elif any(kw in lower_sentence for kw in RISK_KEYWORDS['medium']):
                highlights.append(f"[MEDIUM RISK] {sentence}")

    # If *still* no highlights, just return an info message
    if not highlights and overall_risk == 'Safe':
        highlights = ["No significant risks were automatically detected in the text."]
    elif not highlights:
        highlights = ["Could not automatically extract specific risk clauses, but risk was detected."]


    return overall_risk, highlights[:15] # Return top 15 highlights