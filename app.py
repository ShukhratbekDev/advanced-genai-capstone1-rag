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

# Snapshot original environment to allow reverting/fallback
ORIGINAL_ENV = {
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
    "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN"),
    "GITHUB_REPO": os.environ.get("GITHUB_REPO")
}

def get_effective_config(ui_google_key, ui_gh_token, ui_gh_repo):
    """Priority: UI (if not empty) > ORIGINAL_ENV (Secrets)"""
    return {
        "GOOGLE_API_KEY": ui_google_key.strip() if (ui_google_key and ui_google_key.strip()) else ORIGINAL_ENV["GOOGLE_API_KEY"],
        "GITHUB_TOKEN": ui_gh_token.strip() if (ui_gh_token and ui_gh_token.strip()) else ORIGINAL_ENV["GITHUB_TOKEN"],
        "GITHUB_REPO": ui_gh_repo.strip() if (ui_gh_repo and ui_gh_repo.strip()) else ORIGINAL_ENV["GITHUB_REPO"]
    }

# Pre-initialize RAG on Startup to avoid latency
def initialize_rag(model_name: str = "gemini-2.5-flash"):
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

# Global state to track active configuration
rag_solver = None
active_model = None
active_google_key = None

def get_solver(model_name: str, effective_google_key: str):
    global rag_solver, active_model, active_google_key
    
    needs_init = (rag_solver is None or 
                  model_name != active_model or 
                  effective_google_key != active_google_key)
    
    if needs_init:
        print(f"--- Re-initializing RAG Engine: Model={model_name} ---")
        # Ensure the env var is set for current and downstream (tools) use
        if effective_google_key:
            os.environ["GOOGLE_API_KEY"] = effective_google_key
            
        try:
            rag_solver = RAGHelper(model_name=model_name)
            active_model = model_name
            active_google_key = effective_google_key
            print(f"RAG Engine successfully switched to {model_name}.")
        except Exception as e:
            print(f"Failed to switch model/key: {e}")
            if rag_solver is None:
                return None
    return rag_solver

def chat_logic(message, history, google_key, gh_token, gh_repo, model_name):
    # 1. Resolve Configuration Hierarchy (UI > Secrets)
    config = get_effective_config(google_key, gh_token, gh_repo)
    
    # Sync environment so tools and LangChain see the high-priority values
    for key, val in config.items():
        if val:
            os.environ[key] = val
        else:
            os.environ.pop(key, None) # Remove if both UI and Secret are missing
    
    if not os.environ.get("GOOGLE_API_KEY"):
         yield "⚠️ Please enter your Google API Key in the settings below or set GOOGLE_API_KEY in Space Secrets."
         return

    # 2. Get Engine (handles dynamic switching)
    solver = get_solver(model_name, config["GOOGLE_API_KEY"])
    if not solver:
        yield "❌ System Error: Failed to initialize AI Engine. Please check your API Key."
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
        submit_btn="✈️",
        stop_btn="⏹️",
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
