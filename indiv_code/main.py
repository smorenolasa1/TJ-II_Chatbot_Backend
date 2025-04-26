from fastapi import FastAPI

# Create a single FastAPI instance
app = FastAPI()

# Import and include routers from both apps
from indiv_code.csvllama2 import app as csv_app
from indiv_code.pelletllama2 import app as pellet_app

# Mount the two apps at different endpoints
app.mount("/csv", csv_app)
app.mount("/pellet", pellet_app)

# Health check route (optional)
@app.get("/")
def read_root():
    return {"message": "Unified FastAPI is running!"}