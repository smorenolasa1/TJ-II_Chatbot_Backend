import os
import pandas as pd
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load environment variables
load_dotenv()

# Get Google API Key
google_api_key = os.getenv("GOOGLE_API_KEY")

# Configure Google API Key
genai.configure(api_key=google_api_key)

# Use the correct model
MODEL_NAME = "models/gemini-1.5-pro"

# Store dataset in memory for user queries
stored_df = None

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handles CSV file upload and stores it in memory."""
    global stored_df  # Allow modification of the stored dataset
    
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        stored_df = pd.read_csv(file)  # Store CSV in memory

        return jsonify({"message": "CSV uploaded successfully!"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/ask", methods=["POST"])
def ask_question():
    """Handles user questions based on the uploaded CSV dataset."""
    global stored_df  # Access the stored dataset
    
    try:
        data = request.get_json()
        question = data.get("question")

        if not question:
            return jsonify({"error": "No question provided"}), 400

        if stored_df is None:
            return jsonify({"error": "No dataset uploaded. Please upload a CSV first."}), 400

        # Convert DataFrame to string for AI processing
        csv_data = stored_df.to_csv(index=False)

        # AI query
        query = f"The following CSV data has been uploaded:\n{csv_data}\n\nAnswer this question based on the data: {question}"

        # Get response from Gemini AI
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(query)

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=8501, debug=True)