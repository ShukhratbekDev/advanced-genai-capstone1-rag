# Advanced Generative AI Capstone 1 - RAG Support Agent

**Student:** Shukhratbek Mamadaliev
**Project:** Intelligent Customer Support Agent with RAG & Tool Use

## 1. Project Overview
This project processes technical documentation (Python manuals) and provides an intelligent conversational interface. It uses Retrieval Augmented Generation (RAG) to answer queries based on the provided PDFs and can autonomously create GitHub support tickets when answers are not found.

## 2. Features Implementation Checklist

### Business Features
- [x] **Web Chat UI**: Built with Gradio (`app.py`), supporting conversational history.
- [x] **RAG Q&A**: Uses ChromaDB and Google Gemini (`rag_engine.py`) to answer from `data/*.pdf`.
- [x] **Support Ticket Suggestion**: System prompt instructs to suggest tickets if context is missing.
- [x] **Ticket Creation**: `create_support_ticket` tool defined and bound to LLM.
- [x] **Ticket Fields**: Tool captures Name, Email, Summary, Description.
- [x] **Integration**: Connects to GitHub Issues via `PyGithub`.
- [x] **Citations**: Returns "Source: [file] (Page [x])" with answers.
- [x] **Context Awareness**: System prompt includes "TechSolutions Inc." details.

### Data Requirements
- [x] **7 Documents**: `data/` folder contains 7 files (6 PDFs and 1 TXT) including Library, Tutorial, FAQ, and more.
- [x] **6 PDFs**: Most documents are PDFs.
- [x] **Large Document**: `library.pdf` (Standard Python Library Reference) which is >400 pages.

### Technical Requirements
- [x] **Python**: Fully written in Python 3.
- [x] **Dependencies**: `requirements.txt` included.
- [x] **Vector Storage**: ChromaDB (locally persisted).
- [x] **Function Calling**: Implemented using LangChain tool binding.

### Deployment
- [x] **Hosting**: Hugging Face Spaces.
- [x] **Configuration**: Supports Space Secrets and UI overrides.

## 3. How to Run
1. **Locally**:
   ```bash
   pip install -r requirements.txt
   python data_ingestion.py # Build DB
   python app.py # Launch UI
   ```
2. **Hugging Face Spaces**:
   - Push repository.
   - Set `GOOGLE_API_KEY` in Spaces Secrets.
   - (Optional) Set `GITHUB_TOKEN` and `GITHUB_REPO` for ticket creation.

## 4. Architecture
- **Ingestion**: `data_ingestion.py` splits PDFs using `RecursiveCharacterTextSplitter` and embeds them into `chroma_db`.
- **Engine**: `rag_engine.py` initializes `ChatGoogleGenerativeAI` (Gemini) and the `Chroma` retriever. Tools are bound for function calling.
- **UI**: `app.py` renders the chat interface and manages state.
