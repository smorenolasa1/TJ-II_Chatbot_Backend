import json
import spacy
import re

# File paths
COLUMN_NAMES_FILE = "data/pelletcolumn.txt"
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

    keywords = []
    current_keyword = ""

    for token in doc:
        # Allow NOUN, PROPN, NUM, and VERBS that often act as NOUNs
        if (token.pos_ in {"NOUN", "PROPN", "NUM", "VERB"} or any(char.isdigit() for char in token.text)):
            if token.pos_ == "NUM" and current_keyword:  
                current_keyword += f" {token.text}"  # Merge numbers with previous words
            else:
                if current_keyword:
                    keywords.append(current_keyword)  # Save previous keyword
                current_keyword = token.text.lower()

    if current_keyword:
        keywords.append(current_keyword)  # Add last keyword

    # Ensure we capture domain-specific words (e.g., "descarga") even if spaCy filtered them
    important_words = {"descarga", "inyección", "comentario"}  # Add other common scientific terms
    for token in doc:
        if token.text.lower() in important_words and token.text.lower() not in keywords:
            keywords.append(token.text.lower())

    keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order
    print("\n[DEBUG] NLP Extracted Keywords:", keywords)

    if not keywords:
        print("[DEBUG] No keyword extracted.")
        return None  # No match found

    return keywords

# Normalize column names (convert CamelCase and underscores)
def normalize_column_name(name):
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)  # Split camelCase
    name = name.replace("_", " ")  # Replace underscores with spaces
    return name.lower()

# Retrieve relevant keys based on matched keywords (exact match first, fallback to partial match)
def retrieve_relevant_keys(keywords, column_names):
    keyword_mapping = {}  # Dictionary to store {extracted_keyword: [matching_keys]}

    column_names_lower = {normalize_column_name(col): col for col in column_names}  # Normalize column names

    for keyword in keywords:
        exact_matches = [column_names_lower[col] for col in column_names_lower 
                         if re.search(rf"\b{re.escape(keyword)}\b", col, re.IGNORECASE)]

        if not exact_matches:
            partial_matches = [column_names_lower[col] for col in column_names_lower if keyword in col]
        else:
            partial_matches = []

        matches = exact_matches if exact_matches else partial_matches  # Prefer exact match

        if matches:
            keyword_mapping[keyword] = sorted(matches, key=len)  # Sort by length for relevance

    print(f"\n[DEBUG] Keyword Mapping: {keyword_mapping}")  # Debugging
    return keyword_mapping

# Process user query
def process_query(query, debug=False):
    column_names = load_column_names()
    
    keywords = extract_keywords(query)
    if not keywords:
        return "No matching parameters found."

    relevant_keys = retrieve_relevant_keys(keywords, column_names)

    if not relevant_keys:
        return "No matching parameters found."

    return relevant_keys  # Return dictionary mapping extracted keywords to matching column names