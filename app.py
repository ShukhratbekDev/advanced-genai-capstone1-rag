import gradio as gr
import os
from rag_engine import RAGHelper

# Global Engine Instance
rag_solver = None

def get_solver():
    global rag_solver
    if rag_solver is None:
        try:
            rag_solver = RAGHelper()
        except Exception as e:
            print(f"RAG Init Error: {e}")
            return None
    return rag_solver

def chat_logic(message, history, google_key, gh_token, gh_repo):
    # 1. Configuration
    if not google_key:
        yield "⚠️ Please enter your Google API Key in the settings below to start."
        return

    os.environ["GOOGLE_API_KEY"] = google_key
    if gh_token:
        os.environ["GITHUB_TOKEN"] = gh_token
    if gh_repo:
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
with gr.Blocks(title="TechSolutions Support AI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 TechSolutions Customer Support AI")
    gr.Markdown("Create support tickets on GitHub, query manuals, and get help 24/7.")
    
    with gr.Accordion("⚙️ Settings (API Keys)", open=True):
        with gr.Row():
            google_key_input = gr.Textbox(
                label="Google API Key (Required)",
                placeholder="AIza...",
                type="password"
            )
            gh_token_input = gr.Textbox(
                label="GitHub Token (Optional)",
                placeholder="For ticket creation...",
                type="password"
            )
            gh_repo_input = gr.Textbox(
                label="GitHub Repo (Optional)",
                placeholder="username/repo"
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
    demo.launch()
