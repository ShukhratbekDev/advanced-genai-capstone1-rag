import os
import glob
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = "data"
DB_PATH = "chroma_db_v3"

def load_documents() -> List[Document]:
    documents = []
    
    # Load PDFs
    pdf_files = glob.glob(os.path.join(DATA_PATH, "*.pdf"))
    for pdf_file in pdf_files:
        print(f"Loading PDF: {pdf_file}")
        try:
            loader = PyPDFLoader(pdf_file)
            documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {pdf_file}: {e}")

    # Load Text files
    text_files = glob.glob(os.path.join(DATA_PATH, "*.txt"))
    for text_file in text_files:
        print(f"Loading Text: {text_file}")
        try:
            loader = TextLoader(text_file)
            documents.extend(loader.load())
        except Exception as e:
            print(f"Error loading {text_file}: {e}")
            
    return documents

def ingest_data():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    print("Loading documents...")
    raw_documents = load_documents()
    print(f"Loaded {len(raw_documents)} raw document pages/files.")

    print("Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(raw_documents)
    print(f"Split into {len(chunks)} chunks.")

    print("Creating vector store...")
    # Initialize Google Embeddings (embedding-001 is the standard model)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create and persist ChromaDB
    # Note: Chroma is "serverless" in the sense it runs embedded without a separate server process for this scale
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    print(f"Vector store created at {DB_PATH}")

if __name__ == "__main__":
    ingest_data()
