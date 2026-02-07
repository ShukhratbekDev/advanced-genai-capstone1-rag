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
# Load custom CSS (raw CSS content, no HTML tags)
custom_css = ""
try:
    with open("custom_styles.css", "r") as f:
        custom_css = f.read()
except FileNotFoundError:
    print("Warning: custom_styles.css not found. Using default styles.")


# Use default theme - custom styling via CSS only

with gr.Blocks(title="TechSolutions Support AI v1.1.0") as demo:
    # Header Section
    gr.HTML("""
        <div class="header-container">
            <h1 class="app-title">🤖 TechSolutions Customer Support AI</h1>
            <p class="subtitle">
                Powered by Advanced RAG Technology & Gemini AI
            </p>
        </div>
    """)

    
    # Settings Accordion
    with gr.Accordion("⚙️ Settings & API Configuration", open=False):
        with gr.Row():
            with gr.Column(scale=1):
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
            with gr.Column(scale=1):
                gh_repo_input = gr.Textbox(
                    label="GitHub Repository",
                    placeholder="username/repo (Optional)",
                    info="Format: 'owner/repository'"
                )
                model_dropdown = gr.Dropdown(
                    choices=["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"],
                    value="gemini-2.5-flash",
                    label="AI Model Selection",
                    info="Select the Gemini model to use."
                )

    # Chatbot Interface
    with gr.Column(elem_classes=["group-container"]):
        chatbot_comp = gr.Chatbot(
            placeholder="**TechSolutions Support Assistant**\n\nAsk about documentation, create tickets, or get company info.",
            height=600,
            show_label=False,
            avatar_images=(None, "🤖"),
            elem_classes=["chatbot"]
        )

    # Quick Action Suggestions
    gr.HTML("""
        <div style="margin: 1.5rem 0 0.5rem 0;">
            <p style="font-size: 0.9rem; font-weight: 600; color: var(--neutral-500);">
                💡 Suggested Actions
            </p>
        </div>
    """)
    
    with gr.Row():
        suggestion_1 = gr.Button("🐍 Floating point in Python?", size="sm", elem_classes=["suggestion-btn"])
        suggestion_2 = gr.Button("🎫 Create support ticket", size="sm", elem_classes=["suggestion-btn"])
        suggestion_3 = gr.Button("📞 Company contact info", size="sm", elem_classes=["suggestion-btn"])
        suggestion_4 = gr.Button("📚 Defining functions", size="sm", elem_classes=["suggestion-btn"])

    # Chat Input
    chat_input = gr.Textbox(
        placeholder="Type your question here...", 
        container=True,
        scale=7,
        show_label=False,
        lines=1
    )

    # Chat Interface
    chat_interface = gr.ChatInterface(
        fn=chat_logic,
        chatbot=chatbot_comp,
        additional_inputs=[google_key_input, gh_token_input, gh_repo_input, model_dropdown],
        textbox=chat_input,
        submit_btn="Send",
        stop_btn="Stop",
        cache_examples=False,
    )

    # Wire up the suggestion buttons
    suggestion_1.click(fn=lambda: "How do I use decimal floating point in Python?", outputs=chat_input)
    suggestion_2.click(fn=lambda: "Create a support ticket. My email is user@email.com and the issue is 'Timeout'.", outputs=chat_input)
    suggestion_3.click(fn=lambda: "Who do you work for and what is your contact info?", outputs=chat_input)
    suggestion_4.click(fn=lambda: "What does the tutorial say about defining functions?", outputs=chat_input)
    
    # Footer
    gr.HTML("""
        <div class="footer">
            <p>Built with LangChain, ChromaDB, and Google Gemini AI • v1.1.0</p>
        </div>
    """)
    
if __name__ == "__main__":
    initialize_rag()
    # Launch with SSR disabled for stability
    demo.launch(css=custom_css, ssr_mode=False)


