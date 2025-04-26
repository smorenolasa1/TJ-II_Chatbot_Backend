import json
import spacy
import re
from fuzzywuzzy import process 

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

# Normalization function to handle cases where lemmatization fails
def normalize_word(token):
    """Force lemmatization and manually handle common plural issues."""
    lemma = token.lemma_.lower()
    
    # If lemma and token are the same, apply a basic rule-based singularization
    if lemma == token.text.lower():
        if lemma.endswith("es"):
            return lemma[:-2]  # descargas -> descarga
        elif lemma.endswith("s"):
            return lemma[:-1]  # comentarios -> comentario
    
    return lemma

# Apply fuzzy matching to fix typos
def correct_typos(keyword, valid_words, threshold=80):  # ✅ Lowered threshold for better matches
    """Find the closest word to 'keyword' within 'valid_words' using fuzzy matching."""
    match, score = process.extractOne(keyword, valid_words)  # Find best match
    return match if score >= threshold else keyword  # Only replace if it's a close match

# Extract meaningful keywords from the user query using NLP
def extract_keywords(query, column_names):
    doc = nlp(query)  # Procesar la consulta con spaCy
    keywords = []

    for token in doc:
        word = normalize_word(token)

        # Filtrar solo sustantivos, nombres propios o verbos relevantes
        if token.pos_ in {"NOUN", "PROPN", "VERB"} and not token.is_stop and len(token.text) > 1 and not token.text.isdigit():
            keywords.append(word)

    keywords = list(dict.fromkeys(keywords))  # Eliminar duplicados manteniendo el orden

    # Depuración
    print("\n[DEBUG] NLP Extracted Keywords (Corrected):", keywords)

    return keywords if keywords else None

# Normalize column names (convert CamelCase and underscores)
def normalize_column_name(name):
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)  # Split camelCase
    name = name.replace("_", " ")  # Replace underscores with spaces
    return name.lower().strip()  # ✅ Remove leading/trailing spaces

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
def process_query(query):
    column_names = load_column_names()
    
    keywords = extract_keywords(query, column_names)
    if not keywords:
        return "No matching parameters found."

    relevant_keys = retrieve_relevant_keys(keywords, column_names)

    if not relevant_keys:
        return "No matching parameters found."

    return relevant_keys  # Return dictionary mapping extracted keywords to matching column names
