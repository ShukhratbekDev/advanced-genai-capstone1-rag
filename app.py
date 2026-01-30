import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import gradio as gr
import os
from rag_engine import RAGHelper

# Pre-initialize RAG on Startup to avoid latency
def initialize_rag():
    print("--- Initializing RAG Engine ---")
    if not os.path.exists("chroma_db_v3"):
        if os.environ.get("GOOGLE_API_KEY"):
            print("Database not found. Starting background ingestion...")
            try:
                from data_ingestion import ingest_data
                ingest_data()
            except Exception as e:
                print(f"Startup Ingestion Failed: {e}")
        else:
            print("Warning: GOOGLE_API_KEY missing. Cannot build database.")
    
    # Pre-warm the solver
    global rag_solver
    try:
        from rag_engine import RAGHelper
        rag_solver = RAGHelper()
        print("RAG Engine Ready.")
    except Exception as e:
        print(f"RAG Pre-warm Error: {e}")

# Global Engine Instance
rag_solver = None

def get_solver():
    global rag_solver
    return rag_solver

def chat_logic(message, history, google_key, gh_token, gh_repo):
    # 1. Configuration
    # Prioritize UI input, then env var
    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
    
    if not os.environ.get("GOOGLE_API_KEY"):
         yield "⚠️ Please enter your Google API Key in the settings below or set GOOGLE_API_KEY in Space Secrets."
         return

    if gh_token and gh_token.strip():
        os.environ["GITHUB_TOKEN"] = gh_token
    if gh_repo and gh_repo.strip():
        os.environ["GITHUB_REPO"] = gh_repo

    # 2. Initialize / Get Engine
    solver = get_solver()
    if not solver:
        # Try re-init if key was just provided
        try:
            global rag_solver
            rag_solver = RAGHelper()
            solver = rag_solver
        except Exception as e:
            yield f"❌ System Error: Failed to initialize AI Engine. {e}"
            return

    # 3. Generate Response
    # Convert history for RAG context (list of dicts or tuples? rag_engine expects dicts)
    # Gradio history is [[user, bot], [user, bot]]
    chat_history_dicts = []
    for user_msg, bot_msg in history:
        chat_history_dicts.append({"role": "user", "content": user_msg})
        chat_history_dicts.append({"role": "assistant", "content": bot_msg})
    
    try:
        response_generator = solver.get_response_stream(message, chat_history_dicts)
        
        partial_response = ""
        for chunk in response_generator:
            partial_response += chunk
            yield partial_response
            
    except Exception as e:
        yield f"❌ Error during generation: {str(e)}"

# --- UI Setup ---
with gr.Blocks(title="TechSolutions Support AI v1.1.0", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 TechSolutions Customer Support AI v1.1.0")
    gr.Markdown("Create support tickets on GitHub, query manuals, and get help 24/7.")
    
    with gr.Accordion("⚙️ Settings (API Keys)", open=True):
        with gr.Row():
            google_key_input = gr.Textbox(
                label="Google API Key (Optional if IGNORE_ENV is not set)",
                placeholder="Enter key or use Space Secret",
                type="password"
            )
            gh_token_input = gr.Textbox(
                label="GitHub Token (Optional)",
                placeholder="Enter token or use Space Secret",
                type="password"
            )
            gh_repo_input = gr.Textbox(
                label="GitHub Repo (Optional)",
                placeholder="username/repo (or use Space Secret)"
            )

    chat_interface = gr.ChatInterface(
        fn=chat_logic,
        additional_inputs=[google_key_input, gh_token_input, gh_repo_input],
 
        # Actually standard ChatInterface passes (message, history, *additional_inputs)
        # We'll use default mode which passes history as list of lists
    )
    
    # Customizing ChatInterface is tricky with additional inputs being dynamic properly.
    # The above works, but 'history' arg comes second.
    # `chat_logic` signature matches: (message, history, google, gh, gh)

if __name__ == "__main__":
    initialize_rag()
    demo.launch()
