import json
import spacy

# File paths
COLUMN_NAMES_FILE = "data/column_names.txt"
PARAMETERS_FILE = "data/PARAMETROS_TJ2_model_reduced.json"

# Load spaCy NLP model (Spanish)
nlp = spacy.load("es_core_news_sm")

# Load column names from file
def load_column_names(file_path=COLUMN_NAMES_FILE):
    with open(file_path, "r") as file:
        column_names = [line.strip() for line in file.readlines()]
    return column_names

# Load parameter data from JSON file
def load_json_data(file_path=PARAMETERS_FILE):
    with open(file_path, "r") as file:
        return json.load(file)

# Extract meaningful keywords from the user query using NLP
def extract_keywords(query):
    doc = nlp(query)  # Process query with spaCy

    # Extract valid words (nouns, proper nouns, numbers) and ignore stopwords
    keywords = [
        token.text.lower() for token in doc 
        if (token.pos_ in {"NOUN", "PROPN", "NUM"} or any(char.isdigit() for char in token.text)) 
        and not token.is_stop  # Ignore stopwords
    ]


    keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order
    print("\n[DEBUG] NLP Extracted Keywords:", keywords)
    
    if not keywords:
        print("[DEBUG] No keyword extracted.")
        return None  # No match found

    return keywords

# Retrieve relevant keys based on matched keywords (exact match first, fallback to partial match)
def retrieve_relevant_keys(keywords, column_names):
    keyword_mapping = {}  # Dictionary to store {extracted_keyword: [matching_keys]}

    column_names_lower = {col.lower(): col for col in column_names}  # Lowercase mapping

    for keyword in keywords:
        exact_matches = [column_names_lower[col] for col in column_names_lower if keyword == col]
        partial_matches = [column_names_lower[col] for col in column_names_lower if keyword in col]

        matches = exact_matches if exact_matches else partial_matches  # Prefer exact match

        if matches:
            keyword_mapping[keyword] = matches

    print(f"\n[DEBUG] Keyword Mapping: {keyword_mapping}")  # Debugging
    return keyword_mapping

# Process user query
def process_query(query):
    column_names = load_column_names()
    
    keywords = extract_keywords(query)
    if not keywords:
        return "No matching parameters found."

    relevant_keys = retrieve_relevant_keys(keywords, column_names)

    if not relevant_keys:
        return "No matching parameters found."

    return relevant_keys  # Return dictionary mapping extracted keywords to matching column names
