import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# Patch for Python 3.13 asyncio issue with Gradio/Selectors
import asyncio
import selectors

if sys.version_info >= (3, 13):
    # This is a workaround for the 'Invalid file descriptor: -1' error on shutdown in 3.13
    original_remove_reader = selectors.BaseSelector._remove_reader if hasattr(selectors.BaseSelector, "_remove_reader") else None
    
    def patched_remove_reader(self, fd):
        try:
            return original_remove_reader(self, fd)
        except (ValueError, OSError):
            pass

    if original_remove_reader:
        selectors.BaseSelector._remove_reader = patched_remove_reader

import gradio as gr
import os
from rag_engine import RAGHelper

# Pre-initialize RAG on Startup to avoid latency
def initialize_rag(model_name: str = "gemini-2.0-flash"):
    print(f"--- Initializing RAG Engine with {model_name} ---")
    if not os.path.exists("chroma_db_v4"):
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
        rag_solver = RAGHelper(model_name=model_name)
        print(f"RAG Engine Ready with {model_name}.")
    except Exception as e:
        print(f"RAG Pre-warm Error: {e}")

# Global Engine Instance
rag_solver = None

def get_solver(model_name: str = "gemini-2.5-flash"):
    global rag_solver
    # Ensure model names match (careful with version strings)
    if rag_solver is None or rag_solver.model_name not in [model_name, "gemini-2.0-flash"]:
        print(f"Switching model to {model_name}...")
        try:
            rag_solver = RAGHelper(model_name=model_name)
        except Exception as e:
            print(f"Failed to switch model: {e}")
    return rag_solver

def chat_logic(message, history, google_key, gh_token, gh_repo, model_name):
    # 1. Configuration
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
    solver = get_solver(model_name)
    if not solver:
        try:
            global rag_solver
            rag_solver = RAGHelper(model_name=model_name)
            solver = rag_solver
        except Exception as e:
            yield f"❌ System Error: Failed to initialize AI Engine. {e}"
            return

    # 3. Generate Response
    # Gradio 'history' with type="messages"
    chat_history_dicts = []
    for item in history:
        if isinstance(item, dict):
             chat_history_dicts.append(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            chat_history_dicts.append({"role": "user", "content": item[0]})
            chat_history_dicts.append({"role": "assistant", "content": item[1]})
    
    try:
        response_generator = solver.get_response_stream(message, chat_history_dicts)
        partial_response = ""
        for chunk in response_generator:
            partial_response += chunk
            yield partial_response
    except Exception as e:
        yield f"❌ Error during generation: {str(e)}"

# --- UI Setup ---
with gr.Blocks(title="TechSolutions Support AI v1.1.0") as demo:
    gr.Markdown("# 🤖 TechSolutions Customer Support AI v1.1.0")
    gr.Markdown("Create support tickets on GitHub, query manuals, and get help 24/7.")
    
    with gr.Accordion("⚙️ Settings & API Configuration", open=False):
        google_key_input = gr.Textbox(
            label="Google API Key",
            placeholder="AIza... (Optional if Secret is set)",
            type="password",
            info="Required for Gemini models and Embeddings."
        )
        gh_token_input = gr.Textbox(
            label="GitHub Token",
            placeholder="ghp_... (Optional)",
            type="password",
            info="Needed only for creating support tickets."
        )
        gh_repo_input = gr.Textbox(
            label="GitHub Repo",
            placeholder="username/repo (Optional)",
            info="Format: 'owner/repository'"
        )
        model_dropdown = gr.Dropdown(
            choices=["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"],
            value="gemini-2.5-flash",
            label="AI Model Selection",
            info="Select the Gemini model to use."
        )

    # Simplified Chatbot to avoid version-specific argument errors
    chatbot_comp = gr.Chatbot(
        placeholder="### 🛟 TechSolutions Support Assistant\nAsk about documentation, create tickets, or get company info.",
        height=550
    )

    chat_interface = gr.ChatInterface(
        fn=chat_logic,
        chatbot=chatbot_comp,
        additional_inputs=[google_key_input, gh_token_input, gh_repo_input, model_dropdown],
        textbox=gr.Textbox(placeholder="Ask a question or request a support ticket...", container=False, scale=7),
        # Examples as a list of lists to match the number of inputs (message + additional_inputs)
        examples=[
            ["How do I use decimal floating point in Python?", None, None, None, "gemini-2.5-flash"],
            ["Who do you work for and what is your contact info?", None, None, None, "gemini-2.5-flash"],
            ["What does the tutorial say about defining functions?", None, None, None, "gemini-2.5-flash"],
            ["Create a support ticket. My email is user@email.com and the issue is 'Timeout'.", None, None, None, "gemini-2.5-flash"]
        ],
        cache_examples=False,
    )
    
if __name__ == "__main__":
    initialize_rag()
    # Move theme to launch to resolve Gradio 5+ warning and disable SSR for stability
    demo.launch(theme=gr.themes.Soft(), ssr_mode=False)
