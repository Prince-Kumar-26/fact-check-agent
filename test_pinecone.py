import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME", "fact-check-corpus")

if not api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env file!")

pc = Pinecone(api_key=api_key)

# Check existing indexes
existing_indexes = [idx.name for idx in pc.list_indexes()]
print(f"Existing Indexes in your account: {existing_indexes}")

# Create index if it does not exist
if index_name not in existing_indexes:
    print(f"Creating index '{index_name}'...")
    pc.create_index(
        name=index_name,
        dimension=384,  # Matching sentence-transformers default (all-MiniLM-L6-v2)
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Standard free-tier region
    )
    print(f"Index '{index_name}' successfully created!")
else:
    print(f"Index '{index_name}' already exists and is ready to use.")