from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio

from agent_api import process_query
from data import docs_data

app = FastAPI(title="Secure AI Agent API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Request/Response models
class QueryRequest(BaseModel):
    user_id: str
    question: str

class QueryResponse(BaseModel):
    answer: str
    documents: List[Dict[str, Any]]
    allowed_count: int
    total_count: int

class UserInfo(BaseModel):
    id: str
    name: str
    role: str
    groups: List[str]

class DocumentInfo(BaseModel):
    id: str
    title: str
    category: str
    lang: str

class PermissionInfo(BaseModel):
    user_id: str
    accessible_documents: List[Dict[str, str]]
    groups: List[str]

# User data
USERS = [
    {"id": "user:seigen", "name": "Seigen", "role": "CEO", "groups": ["engineering", "sales"]},
    {"id": "user:alan", "name": "Alan", "role": "EM", "groups": ["engineering"]},
    {"id": "user:tsukada", "name": "Tsukada", "role": "CRO", "groups": ["sales"]},
    {"id": "user:tsuki", "name": "Tsuki", "role": "Backend", "groups": ["engineering"]},
]

# Document to folder mapping (from fga_setup.py)
DOC_TO_FOLDER = {
    "1": "engineering",
    "2": "sales",
    "3": "general",
    "4": "engineering",
    "5": "sales",
    "6": "general",
    "7": "executive",
}

# User to accessible folders mapping
USER_ACCESSIBLE_FOLDERS = {
    "user:seigen": ["engineering", "sales", "general", "executive"],
    "user:alan": ["engineering", "general"],
    "user:tsukada": ["sales", "general"],
    "user:tsuki": ["engineering", "general"],
}

@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")

@app.post("/api/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Process a query with authorization checks.
    """
    try:
        result = await process_query(request.user_id, request.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users", response_model=List[UserInfo])
async def get_users():
    """
    Get list of all users.
    """
    return [UserInfo(**user) for user in USERS]

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """
    Get list of all documents.
    """
    documents = []
    for doc in docs_data:
        documents.append(DocumentInfo(
            id=doc["id"],
            title=doc["metadata"]["title"],
            category=doc["metadata"]["category"],
            lang=doc["metadata"]["lang"]
        ))
    return documents

@app.get("/api/permissions/{user_id}", response_model=PermissionInfo)
async def get_permissions(user_id: str):
    """
    Get permission information for a specific user.
    """
    # Find user
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get accessible folders
    accessible_folders = USER_ACCESSIBLE_FOLDERS.get(user_id, [])
    
    # Get accessible documents
    accessible_documents = []
    for doc in docs_data:
        doc_id = doc["id"]
        folder = DOC_TO_FOLDER.get(doc_id)
        if folder in accessible_folders:
            accessible_documents.append({
                "id": doc_id,
                "title": doc["metadata"]["title"],
                "folder": folder
            })
    
    return PermissionInfo(
        user_id=user_id,
        accessible_documents=accessible_documents,
        groups=user["groups"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

