import os
import uuid
import wikipedia
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Load Environment Variables
load_dotenv()  # Pointing to the root .env file

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fact-check-corpus")

if not PINECONE_API_KEY:
    raise ValueError("Missing PINECONE_API_KEY. Check your .env file.")

# 2. Initialize Pinecone & Embedding Model
print("Initializing Pinecone and loading embedding model (this may take a moment)...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# all-MiniLM-L6-v2 generates the 384-dimensional vectors we configured in Pinecone
model = SentenceTransformer('all-MiniLM-L6-v2') 

# 3. Setup Text Splitter (Chunking)
# We break long articles into 1000-character chunks with a 100-character overlap for context
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len
)

# 4. Define our Seed Dataset (Science, Health, India-specific)
seed_topics = [
    "Vaccine efficacy", 
    "Climate change consensus", 
    "Indian Space Research Organisation", 
    "Ayushman Bharat Yojana",
    "Genetically modified food controversies"
]

def ingest_wikipedia_articles(topics):
    for topic in topics:
        print(f"\nFetching Wikipedia article: {topic}...")
        try:
            # Fetch article content
            page = wikipedia.page(topic, auto_suggest=False)
            text = page.content
            url = page.url
            
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            print(f"Created {len(chunks)} chunks for '{topic}'. Generating embeddings...")
            
            # Prepare vectors for Pinecone
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                # Generate embedding for the chunk
                embedding = model.encode(chunk).tolist()
                
                # Create a unique ID for the chunk
                chunk_id = f"{topic.replace(' ', '_')}_chunk_{i}-{uuid.uuid4().hex[:6]}"
                
                # Attach the mandatory metadata
                metadata = {
                    "title": page.title,
                    "url": url,
                    "domain": "Wikipedia",
                    "text_chunk": chunk
                }
                
                vectors_to_upsert.append((chunk_id, embedding, metadata))
            
            # Upsert in batches of 50 to respect API limits
            batch_size = 50
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch)
                
            print(f"✅ Successfully ingested '{topic}' into Pinecone!")
            
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"⚠️ Disambiguation error for {topic}: {e.options}")
        except Exception as e:
            print(f"❌ Error processing {topic}: {e}")

# 5. Run the ingestion
if __name__ == "__main__":
    print("Starting Knowledge Base Ingestion Pipeline...")
    ingest_wikipedia_articles(seed_topics)
    print("\n🎉 Phase 1.2 Complete: All static data has been ingested!")