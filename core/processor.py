from transformers import pipeline
import torch

# Initialize pipelines (this will download models the first time)
try:
    summarizer = pipeline("summarization", model="t5-small")
    
    # Map of languages to model names
    TRANSLATORS = {
        'bengali': pipeline("translation_en_to_bn", model="shhossain/opus-mt-en-to-bn"),
        'french': pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr"),
        'russian': pipeline("translation_en_to_ru", model="Helsinki-NLP/opus-mt-en-ru"),
        'hindi': pipeline("translation_en_to_hi", model="Helsinki-NLP/opus-mt-en-hi"), # <-- This line is now fixed
        'tamil': pipeline("translation_en_to_ta", model="aryaumesh/english-to-tamil"),
    }
    MODELS_LOADED = True
except Exception as e:
    print(f"Error loading Hugging Face models: {e}")
    MODELS_LOADED = False

def summarize_text(text, max_length=200, min_length=50):
    """
    Generates a summary of the text by summarizing the first 1000 words.
    """
    if not MODELS_LOADED:
        return "Error: Summarization model not loaded."

    # --- NEW SIMPLIFIED LOGIC ---
    # Truncate the text to the first 1000 words
    words = text.split()
    truncated_text = ' '.join(words[:1000])
    
    # Summarize only that truncated text
    try:
        summary = summarizer(truncated_text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Error: Could not produce summary."


def translate_text(text, target_language='bengali'):
    """Translates text to the target language, handling long inputs."""
    if not MODELS_LOADED:
        return "Error: Translation models not loaded."
        
    if target_language not in TRANSLATORS:
        return f"Error: Translation for '{target_language}' is not supported."
    
    translator = TRANSLATORS[target_language]
    
    # --- CHUNKING LOGIC ---
    # This logic will still work perfectly, as it will now only receive
    # the short ~200-word summary, which is well below the chunk limit.
    max_chunk_length = 400 # Approx words, safely under the token limit
    
    words = text.split()
    text_chunks = [' '.join(words[i:i + max_chunk_length]) for i in range(0, len(words), max_chunk_length)]
    
    translated_chunks = []
    
    # Translate each chunk one by one
    for chunk in text_chunks:
        try:
            translation = translator(chunk, max_length=512) 
            translated_chunks.append(translation[0]['translation_text'])
        except Exception as e:
            print(f"Error during translation chunk: {e}")
            translated_chunks.append(f"[Translation Error for this section]")
    
    # Join the translated chunks back together
    return ' '.join(translated_chunks)