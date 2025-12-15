import os
import json
import asyncio
from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.models import WriteAuthorizationModelRequest
from openfga_sdk.client.models import ClientTuple

# Configuration
FGA_API_URL = os.getenv("FGA_API_URL", "http://localhost:8080")
STORE_NAME = "AgentAuthDemo"

async def main():
    print(f"Connecting to OpenFGA at {FGA_API_URL}...")
    
    # 1. Initialize Client
    config = ClientConfiguration(
        api_url=FGA_API_URL,
    )
    
    # We need a temporary client to create the store
    async with OpenFgaClient(config) as client:
        print("Creating Store...")
        store = await client.create_store(body={"name": STORE_NAME})
        store_id = store.id
        print(f"Store created: {store_id}")

    # 2. Re-initialize client with Store ID
    config.store_id = store_id
    async with OpenFgaClient(config) as client:
        
        # 3. Define Authorization Model
        # Load from JSON file
        print("Reading Authorization Model from auth_model.json...")
        with open("auth_model.json", "r") as f:
            model_data = json.load(f)
        
        print("Writing Authorization Model...")
        
        auth_model_response = await client.write_authorization_model(
            body=model_data 
        )
        model_id = auth_model_response.authorization_model_id
        print(f"Authorization Model written: {model_id}")
        
        # 4. Write Tuples (Permissions)
        tuples = [
            # 1. Group Memberships
            # Engineering Group
            ClientTuple(user="user:alan", relation="member", object="group:engineering"),
            ClientTuple(user="user:tsuki", relation="member", object="group:engineering"),
            ClientTuple(user="user:seigen", relation="member", object="group:engineering"), # CEO is in all groups or has direct access
            
            # Sales Group
            ClientTuple(user="user:tsukada", relation="member", object="group:sales"),
            ClientTuple(user="user:seigen", relation="member", object="group:sales"),
            
            # 2. Folder Permissions
            # Engineering Folder -> Viewable by Engineering Group
            ClientTuple(user="group:engineering#member", relation="viewer", object="folder:engineering"),
            
            # Sales Folder -> Viewable by Sales Group
            ClientTuple(user="group:sales#member", relation="viewer", object="folder:sales"),
            
            # General Folder -> Viewable by Everyone (both groups)
            ClientTuple(user="group:engineering#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:sales#member", relation="viewer", object="folder:general"),
            
            # Executive Folder -> Viewable by Seigen only (Direct assignment)
            ClientTuple(user="user:seigen", relation="viewer", object="folder:executive"),

            # 3. Document Hierarchy (Parent Folders)
            # Engineering Docs
            ClientTuple(user="folder:engineering", relation="parent", object="document:1"), # Eng Roadmap
            ClientTuple(user="folder:engineering", relation="parent", object="document:4"), # Project Alpha (JA)
            
            # Sales Docs
            ClientTuple(user="folder:sales", relation="parent", object="document:2"), # Sales Targets
            ClientTuple(user="folder:sales", relation="parent", object="document:5"), # Sales Report (JA)
            
            # General Docs
            ClientTuple(user="folder:general", relation="parent", object="document:3"), # Public Notice
            ClientTuple(user="folder:general", relation="parent", object="document:6"), # Remote Work (JA)
            
            # Executive Docs
            ClientTuple(user="folder:executive", relation="parent", object="document:7"), # Merger Strategy
        ]
        
        print("Writing Tuples...")
        await client.write_tuples(
            body=tuples
        )
        print("Tuples written successfully!")
        
        print("\n--- Setup Complete ---")
        print(f"export FGA_STORE_ID={store_id}")
        print("Please set this environment variable before running the agent.")

if __name__ == "__main__":
    asyncio.run(main())
