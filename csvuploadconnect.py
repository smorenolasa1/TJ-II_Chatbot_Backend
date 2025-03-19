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

# Store dataset
stored_df = None
MAX_ROWS = 500  # Limit for Gemini AI

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handles CSV file upload and stores the dataset."""
    global stored_df

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        stored_df = pd.read_csv(file)  # Store full dataset
        total_rows = len(stored_df)

        return jsonify({
            "message": "CSV uploaded successfully!",
            "total_rows": total_rows,
            "max_rows": MAX_ROWS  # Inform frontend of the AI limit
        })

    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500


@app.route("/ask", methods=["POST"])
def ask_question():
    """Handles user questions based on the selected dataset range."""
    global stored_df

    try:
        data = request.get_json()
        question = data.get("question")
        start_row = int(data.get("start_row", 0))  # Default start from 0
        end_row = int(data.get("end_row", MAX_ROWS))  # Default to max limit

        if not question:
            return jsonify({"error": "No question provided"}), 400

        if stored_df is None:
            return jsonify({"error": "No dataset uploaded. Please upload a CSV first."}), 400

        # Limit row selection to prevent errors
        total_rows = len(stored_df)
        if start_row < 0 or end_row > total_rows or start_row >= end_row:
            return jsonify({"error": "Invalid row range selected."}), 400

        # Select the user-defined range
        selected_df = stored_df.iloc[start_row:end_row]

        # Convert DataFrame to text for AI processing
        csv_data = selected_df.to_csv(index=False)

        # If dataset is larger than MAX_ROWS, inform user
        too_large_message = ""
        if total_rows > MAX_ROWS:
            too_large_message = f"⚠️ Your dataset has {total_rows} rows. For now, we can only process {MAX_ROWS} rows at a time. Adjust the range using the timeline."

        # AI query
        query = f"""
        The following CSV data (rows {start_row} to {end_row}) has been uploaded:
        
        {csv_data}
        
        ### Instructions:
        - Analyze the data carefully and answer the following question:
        **{question}**
        - Present the answer in a well-structured format.
        - Use bullet points (`-`) for lists.
        - Use bold (`**`) for important values.
        - Use subheadings (##) if necessary.
        - Ensure clarity and avoid unnecessary repetition.

        """

        # Send request to Gemini AI
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(query)

        return jsonify({"response": response.text, "warning": too_large_message})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=8501, debug=True)