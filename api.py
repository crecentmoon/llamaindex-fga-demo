from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import os
from dotenv import load_dotenv

from agent_api import process_query, fga_config
from data import docs_data, USERS, DOC_TO_FOLDER, get_user_by_id, get_profile_image_path
from openfga_sdk import OpenFgaClient
from openfga_sdk.client.models import ClientCheckRequest

load_dotenv()

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
    profile_image: str

class DocumentInfo(BaseModel):
    id: str
    title: str
    category: str
    lang: str
    folder: str

class PermissionInfo(BaseModel):
    user_id: str
    accessible_documents: List[Dict[str, str]]
    groups: List[str]

# All data is now imported from data.py (Single Source of Truth)

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
    users_with_images = []
    for user in USERS:
        user_dict = user.copy()
        user_dict["profile_image"] = get_profile_image_path(user["id"])
        users_with_images.append(UserInfo(**user_dict))
    return users_with_images

@app.get("/api/documents", response_model=List[DocumentInfo])
async def get_documents():
    """
    Get list of all documents.
    """
    documents = []
    for doc in docs_data:
        doc_id = doc["id"]
        folder = DOC_TO_FOLDER.get(doc_id, "unknown")
        documents.append(DocumentInfo(
            id=doc_id,
            title=doc["metadata"]["title"],
            category=doc["metadata"]["category"],
            lang=doc["metadata"]["lang"],
            folder=folder
        ))
    return documents

@app.get("/api/permissions/{user_id}", response_model=PermissionInfo)
async def get_permissions(user_id: str):
    """
    Get permission information for a specific user from OpenFGA.
    """
    # Find user
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions for each document using OpenFGA
    accessible_documents = []
    
    async with OpenFgaClient(fga_config) as client:
        for doc in docs_data:
            doc_id = doc["id"]
            object_str = f"document:{doc_id}"
            
            try:
                response = await client.check(
                    body=ClientCheckRequest(
                        user=user_id,
                        relation="viewer",
                        object=object_str
                    )
                )
                
                if response.allowed:
                    folder = DOC_TO_FOLDER.get(doc_id, "unknown")
                    accessible_documents.append({
                        "id": doc_id,
                        "title": doc["metadata"]["title"],
                        "folder": folder
                    })
            except Exception as e:
                # Log error but continue processing other documents
                print(f"Error checking permission for {object_str}: {e}")
                continue
    
    return PermissionInfo(
        user_id=user_id,
        accessible_documents=accessible_documents,
        groups=user["groups"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

