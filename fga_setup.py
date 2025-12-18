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
            # Engineering Group (Management level)
            ClientTuple(user="user:alan", relation="member", object="group:engineering"),
            ClientTuple(user="user:seigen", relation="member", object="group:engineering"), # CEO is in all groups
            
            # SE Group (Software Engineers)
            ClientTuple(user="user:kuyama", relation="member", object="group:se"),
            ClientTuple(user="user:shibata", relation="member", object="group:se"),
            
            # Sales Group
            ClientTuple(user="user:tsukada", relation="member", object="group:sales"),
            ClientTuple(user="user:ando", relation="member", object="group:sales"),
            ClientTuple(user="user:seigen", relation="member", object="group:sales"),
            
            # Product Group
            ClientTuple(user="user:alan", relation="member", object="group:product"), # EM oversees Product team
            ClientTuple(user="user:kristine", relation="member", object="group:product"),
            ClientTuple(user="user:nakajima", relation="member", object="group:product"),
            ClientTuple(user="user:seigen", relation="member", object="group:product"),
            
            # Corporate Group
            ClientTuple(user="user:ikeuchi", relation="member", object="group:corporate"),
            ClientTuple(user="user:jinnai", relation="member", object="group:corporate"),
            ClientTuple(user="user:seigen", relation="member", object="group:corporate"),
            
            # SC/PM Team (Cross-functional team)
            ClientTuple(user="user:kurauchi", relation="member", object="group:scpm"),
            
            # Note: tsukioka (Hacker) has no group memberships - no access
            
            # 2. Folder Permissions
            # Engineering Folder -> Viewable by Engineering Group and SE Group
            ClientTuple(user="group:engineering#member", relation="viewer", object="folder:engineering"),
            ClientTuple(user="group:se#member", relation="viewer", object="folder:engineering"),
            
            # Sales Folder -> Viewable by Sales Group
            ClientTuple(user="group:sales#member", relation="viewer", object="folder:sales"),
            
            # Product Folder -> Viewable by Product Group
            ClientTuple(user="group:product#member", relation="viewer", object="folder:product"),
            
            # Corporate Folder -> Viewable by Corporate Group
            ClientTuple(user="group:corporate#member", relation="viewer", object="folder:corporate"),
            
            # SC/PM Folder -> Viewable by SC/PM Team
            ClientTuple(user="group:scpm#member", relation="viewer", object="folder:scpm"),
            
            # General Folder -> Viewable by Everyone (all groups)
            ClientTuple(user="group:engineering#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:se#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:sales#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:product#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:corporate#member", relation="viewer", object="folder:general"),
            ClientTuple(user="group:scpm#member", relation="viewer", object="folder:general"),
            
            # Executive Folder -> Viewable by Seigen only (Direct assignment)
            ClientTuple(user="user:seigen", relation="viewer", object="folder:executive"),
            
            # Cross-functional access for deeper relationships
            # Product Group can view Engineering folder (for collaboration docs like document:12)
            ClientTuple(user="group:product#member", relation="viewer", object="folder:engineering"),
            
            # Sales Group can view Product folder (for collaboration docs like document:13)
            ClientTuple(user="group:sales#member", relation="viewer", object="folder:product"),

            # 3. Document Hierarchy (Parent Folders)
            # Engineering Docs
            ClientTuple(user="folder:engineering", relation="parent", object="document:1"), # Eng Roadmap
            ClientTuple(user="folder:engineering", relation="parent", object="document:4"), # Project Alpha (JA)
            ClientTuple(user="folder:engineering", relation="parent", object="document:12"), # Engineering-Product Collaboration
            
            # Sales Docs
            ClientTuple(user="folder:sales", relation="parent", object="document:2"), # Sales Targets
            ClientTuple(user="folder:sales", relation="parent", object="document:5"), # Sales Report (JA)
            ClientTuple(user="folder:sales", relation="parent", object="document:13"), # Sales-Product Feedback
            
            # Product Docs
            ClientTuple(user="folder:product", relation="parent", object="document:8"), # Product Roadmap
            ClientTuple(user="folder:product", relation="parent", object="document:9"), # New Feature Release Plan
            
            # Corporate Docs
            ClientTuple(user="folder:corporate", relation="parent", object="document:10"), # Corporate Policy Update
            ClientTuple(user="folder:corporate", relation="parent", object="document:11"), # HR System Review
            ClientTuple(user="folder:corporate", relation="parent", object="document:14"), # Security Incident Response
            
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
