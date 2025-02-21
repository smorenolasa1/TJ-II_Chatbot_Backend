import json
import spacy

# File paths
COLUMN_NAMES_FILE = "data/column_names.txt"
PARAMETERS_FILE = "data/PARAMETROS_TJ2_model_reduced.json"

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load column names from file
def load_column_names(file_path=COLUMN_NAMES_FILE):
    with open(file_path, "r") as file:
        column_names = [line.strip() for line in file.readlines()]
    return column_names

# Load parameter data from JSON file
def load_json_data(file_path=PARAMETERS_FILE):
    with open(file_path, "r") as file:
        return json.load(file)

# Extract the best keyword from the user query using NLP
def extract_keyword(query, column_names):
    doc = nlp(query)  # Process query with spaCy

    # Extract nouns, proper nouns, or words with numbers (e.g., "ECRH1")
    keywords = [token.text for token in doc if token.pos_ in {"NOUN", "PROPN"} or any(char.isdigit() for char in token.text)]
    
    print("\n[DEBUG] NLP Extracted Keywords:", keywords)

    # Find the best match in column names
    for keyword in keywords:
        exact_matches = [col for col in column_names if keyword.lower() == col.lower()]
        if exact_matches:
            print(f"[DEBUG] Exact match found: {keyword}")
            return keyword  # Return exact match if found

    for keyword in keywords:
        partial_matches = [col for col in column_names if keyword.lower() in col.lower()]
        if partial_matches:
            print(f"[DEBUG] Partial match found: {keyword}")
            return keyword  # Return first valid keyword found

    print("[DEBUG] No keyword extracted.")
    return None  # No match found

# Retrieve relevant keys based on an exact keyword match
def retrieve_relevant_keys(keyword, column_names):
    matches = [key for key in column_names if keyword.lower() in key.lower()]
    print(f"\n[DEBUG] Matching keys for '{keyword}':", matches)  # Debugging
    return matches

# Process user query
def process_query(query):
    column_names = load_column_names()
    
    keyword = extract_keyword(query, column_names)
    if not keyword:
        return "No matching parameters found."

    relevant_keys = retrieve_relevant_keys(keyword, column_names)

    if len(relevant_keys) == 0:
        return "No matching parameters found."

    return relevant_keys  # Return all matching column names

# Example query
query = "cometario?"
result = process_query(query)
print("\n[FINAL RESULT]:", result)  # Expected: Only parameters containing "ECRH1"