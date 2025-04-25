import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List, Dict, Any

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Configure Google API Key
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Use the correct model
MODEL_NAME = "models/gemini-1.5-pro"

@app.post("/generate_report")
async def generate_report(request: Request):
    try:
        data = await request.json()

        # Ensure we have interactions to summarize
        interactions: List[Dict[str, Any]] = data.get("interactions", [])
        if not interactions:
            raise HTTPException(status_code=400, detail="No interactions provided")

        # Create a structured input for Gemini AI
        interactions_text = "\n\n".join([
            f"Interaction {index + 1}:\n"
            f"Tool Used: {interaction.get('tool', 'Unknown')}\n"
            f"User Query: {interaction.get('query', 'N/A')}\n"
            f"AI Response: {interaction.get('response', 'N/A')}\n"
            f"Plot URL: {interaction.get('plot', 'N/A')}\n"
            for index, interaction in enumerate(interactions)
        ])

        prompt = f"""
        You are an AI model designed to generate daily reports based on interactions between the user and various tools.
        
        The following are the interactions for the day:

        {interactions_text}

        Please generate a detailed, structured report summarizing the interactions. The report should include:
        - A list of all user queries and their corresponding responses.
        - Details of the plots generated, if any.
        - Any important insights or conclusions that can be derived from the interactions.
        - Present the report in a clear, organized, and readable format.
        """

        # Send the prompt to Gemini AI
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        generated_report = response.text.strip()

        return JSONResponse(content={"report": generated_report})

    except Exception as e:
        print(f"❌ Error in /generate_report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")