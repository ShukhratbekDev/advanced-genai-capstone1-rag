---
title: Advanced Genai Capstone1 Rag
emoji: 🚀
colorFrom: purple
colorTo: gray
sdk: gradio
sdk_version: 6.5.1
app_file: app.py
pinned: false
license: mit
---

# Advanced Generative AI - Capstone Project 1 Report
**Student**: Antigravity AI
**Course**: Advanced Generative AI

## 1. Project Overview
This solution is a **premium Customer Support RAG system** designed for "TechSolutions Inc." It features a modern, glassmorphic UI that allows users to query technical manuals and policies with an exceptional user experience. If a solution is not found, the system intelligently creates a support ticket.

### ✨ Design Highlights
- **Modern Glassmorphic UI**: Premium dark theme with blur effects and vibrant gradients
- **Smooth Animations**: Delightful micro-interactions and transitions
- **Responsive Design**: Optimized for desktop and mobile devices
- **Professional Aesthetics**: Purple-indigo gradient color scheme with Inter typography
- **Enhanced UX**: Quick action buttons, emoji icons, and intuitive layout

See [DESIGN_IMPROVEMENTS.md](DESIGN_IMPROVEMENTS.md) for detailed design documentation.

## 2. Technical Architecture
- **Language**: Python 3.10+
- **Frameworks**: LangChain, ChromaDB, **Gradio 6.5+**
- **LLM**: Google Gemini 3 Flash Preview (via `langchain-google-genai`)
- **Embeddings**: Google Generative AI Embeddings (`models/embedding-001`)
- **Integration**: GitHub API (via `PyGithub`) for ticket creation
- **UI**: Custom CSS with glassmorphism, gradients, and animations

### Key Components
1.  **Data Ingestion (`data_ingestion.py`)**:
    -   Loads PDFs/Text from `data/`
    -   Chunks and stores embeddings in ChromaDB (Serverless/Embedded)
2.  **RAG Engine (`rag_engine.py`)**:
    -   Retrieves relevant chunks and enforces citation
    -   **GitHub Integration**: Uses `GITHUB_TOKEN` and `GITHUB_REPO`
3.  **User Interface (`app.py`)**:
    -   **Premium Gradio** Web UI with custom styling
    -   Chat Interface with settings for `GOOGLE_API_KEY`, `GITHUB_TOKEN`, and `GITHUB_REPO`
    -   Glassmorphic design with smooth animations
4.  **Custom Styling (`custom_styles.css`)**:
    -   400+ lines of custom CSS
    -   Modern color system with gradients
    -   Responsive design and animations

## 3. Data Sources Used
-   `data/library.pdf` (Primary Technical Manual)
-   `data/tutorial.pdf` (Secondary Manual)
-   `data/company_policies.txt` (Internal Docs)

## 4. Quick Start

### Option 1: Using the Start Script (Recommended)
```bash
./start.sh
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Ingest data (first time only)
python data_ingestion.py

# Launch the application
python app.py
```

The application will open at `http://localhost:7860`

## 5. Configuration

### Environment Variables
Create a `.env` file or use the UI settings:
```env
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=your_github_token_here  # Optional
GITHUB_REPO=username/repository      # Optional
```

### UI Configuration
All settings can be configured through the **⚙️ Settings & API Configuration** accordion in the web interface.

## 6. Deployment (Hugging Face Spaces)

### Automated Deployment
```bash
python deploy_to_hf.py
```

### Manual Deployment
1. Upload all files to your Hugging Face Space
2. Set secrets in Space settings:
   - `GOOGLE_API_KEY` (Required)
   - `GITHUB_TOKEN` (Optional)
   - `GITHUB_REPO` (Optional)

### Note on Dependencies
The `pysqlite3-binary` package in `requirements.txt` is only needed for Hugging Face Spaces. For local development, it can be skipped.

## 7. Features

### 🤖 AI-Powered Support
- Context-aware responses using RAG technology
- Multi-document knowledge base
- Citation-backed answers

### 🎫 Ticket Creation
- Automatic GitHub issue creation
- Email and issue description extraction
- Seamless integration with GitHub API

### 🎨 Premium UI/UX
- Glassmorphic design language
- Smooth animations and transitions
- Dark theme with vibrant gradients
- Responsive layout
- Quick action suggestions
- Multiple AI model selection

### ⚡ Performance
- Streaming responses for real-time feedback
- Efficient vector search with ChromaDB
- Optimized embeddings

## 8. Project Structure
```
.
├── app.py                          # Main Gradio application
├── rag_engine.py                   # RAG logic and GitHub integration
├── data_ingestion.py               # Data loading and embedding
├── custom_styles.css               # Premium UI styling
├── requirements.txt                # Python dependencies
├── deploy_to_hf.py                # Hugging Face deployment script
├── start.sh                        # Quick start script
├── DESIGN_IMPROVEMENTS.md          # Design documentation
├── data/                           # Knowledge base documents
│   ├── library.pdf
│   ├── tutorial.pdf
│   └── company_policies.txt
└── chroma_db_v4/                   # Vector database (generated)
```

## 9. Technology Stack
- **LangChain**: RAG orchestration
- **ChromaDB**: Vector database
- **Google Gemini**: Large language model
- **Gradio**: Web interface framework
- **PyGithub**: GitHub API integration
- **Custom CSS**: Premium styling

## 10. License
MIT License - See LICENSE file for details

