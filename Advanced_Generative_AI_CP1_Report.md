# Advanced Generative AI - Capstone Project 1 Report
**Student**: Antigravity AI
**Course**: Advanced Generative AI

## 1. Project Overview
This solution is a specific Customer Support RAG system designed for "TechSolutions Inc." It allows users to query technical manuals and policies. If a solution is not found, the system intelligently creates a support ticket.

## 2. Technical Architecture
- **Language**: Python 3.10
- **Frameworks**: LangChain, ChromaDB, **Gradio**
- **LLM**: Google Gemini 3 Flash Preview (model=`gemini-3-flash-preview`)
- **Embeddings**: Google Generative AI Embeddings (`models/embedding-001`)
- **Integration**: GitHub API (via `PyGithub`) for ticket creation.

### Key Components
1.  **Data Ingestion (`data_ingestion.py`)**:
    -   Loads PDFs/Text from `data/`.
    -   Chunks and stores embeddings in ChromaDB (Serverless/Embedded).
2.  **RAG Engine (`rag_engine.py`)**:
    -   Retrieves relevant chunks and enforces citation.
    -   **GitHub Integration**: Uses `GITHUB_TOKEN` and `GITHUB_REPO`.
3.  **User Interface (`app.py`)**:
    -   **Gradio** Web UI.
    -   Chat Interface with settings for `GOOGLE_API_KEY`, `GITHUB_TOKEN`, and `GITHUB_REPO`.

## 3. Data Sources Used
-   `data/library.pdf` (Primary Technical Manual)
-   `data/tutorial.pdf` (Secondary Manual)
-   `data/company_policies.txt` (Internal Docs)

## 4. Deployment (Hugging Face Spaces)
The solution is designed for **Gradio** Spaces.

1.  **Run Deployment Script**: 
    ```bash
    pip install huggingface_hub
    python deploy_to_hf.py
    ```

2.  **Manual Method**:
    -   Create a new Space (Select **Gradio** SDK).
    -   Upload all files (`app.py`, `rag_engine.py`, `data_ingestion.py`, `requirements.txt`, `data/`).

3.  **Secrets**: 
    -   Add `GOOGLE_API_KEY` in Spaces Settings.
    -   (Optional) Add `GITHUB_TOKEN` and `GITHUB_REPO`.

## 5. Verification
To verify locally:
1.  `pip install -r requirements.txt`
2.  `python data_ingestion.py`
3.  `python app.py` (Launches a local Gradio URL).
