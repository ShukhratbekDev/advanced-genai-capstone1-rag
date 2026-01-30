import os
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from dotenv import load_dotenv
from github import Github

load_dotenv()

DB_PATH = "chroma_db_v4"

# Global fallback for environment variables
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO") # Format: "username/repo"

# --- 1. Tool Definition ---
@tool
def create_support_ticket(user_name: str, user_email: str, issue_summary: str, issue_description: str) -> str:
    """
    Creates a support ticket on GitHub Issues.
    Use this tool when the user explicitly asks to create a ticket OR when the answer cannot be found in the documentation.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPO")

    if not token or not repo_name:
        return f"Error: GitHub configuration missing. Required: GITHUB_TOKEN and GITHUB_REPO. (Current Repo: {repo_name})"

    # Clean repo name in case a full URL was pasted
    repo_name = repo_name.replace("https://github.com/", "").strip("/")
    
    print(f"!!! CREATING TICKET in {repo_name} for {user_email} !!!")

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Create full description with user info
        full_body = f"**User**: {user_name} ({user_email})\n\n**Description**:\n{issue_description}\n\n*Created via AI Agent*"
        
        issue = repo.create_issue(
            title=issue_summary,
            body=full_body,
            labels=["support", "ai-generated"]
        )
        
        return f"Success! GitHub Issue created: {issue.html_url} (Issue #{issue.number})"
    except Exception as e:
        return f"Failed to create GitHub issue: {str(e)}"

# --- 2. RAG Chain Setup ---
class RAGHelper:
    def __init__(self):
        # Using Google Embeddings
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        if os.path.exists(DB_PATH):
            self.vectorstore = Chroma(
                persist_directory=DB_PATH, 
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
        else:
            self.vectorstore = None
            self.retriever = None

        # User requested specific model
        self.llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
        self.llm_with_tools = self.llm.bind_tools([create_support_ticket])

        # System prompt with Company Info and Citation instructions
        self.system_prompt = """You are a helpful customer support assistant for TechSolutions Inc. 
        
        Company Contact Info:
        - Phone: +1-800-555-0199
        - Email: support@techsolutions.fake
        
        Instructions:
        1. Answer the user's question using ONLY the provided context.
        2. If the answer is found in the context, you MUST cite the document name and page number as [Source: file_name, Page: X].
        3. If the answer is NOT found in the context, strictly state that you couldn't find the answer and suggest creating a support ticket.
        4. If the user asks to create a ticket, collect necessary details (Name, Email, Summary, Description) if not provided, and call the create_support_ticket tool.
        """

    def format_docs(self, docs):
        """Format retrieved documents with source metadata."""
        formatted = []
        for doc in docs:
            source = doc.metadata.get('source', 'unknown')
            page = doc.metadata.get('page', 'unknown')
            content = doc.page_content.replace('\n', ' ')
            formatted.append(f"Content: {content}\nSource: {source} (Page {page})")
        return "\n\n".join(formatted)

    def get_response_stream(self, query: str, chat_history: List[Dict] = []):
        """
        Generates a response using RAG and Tool Calling.
        """
        if not self.retriever:
            yield "System Error: Knowledge base not loaded. Please ensure data is ingested."
            return

        # 1. Retrieve Context
        try:
            docs = self.retriever.invoke(query)
            context_str = self.format_docs(docs)
        except Exception as e:
            yield f"Retrieval Error: {e}"
            return

        # 2. Construct Messages
        messages = [
            ("system", self.system_prompt),
            ("system", f"Context available:\n{context_str}"),
        ]
        
        # Add history
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append((role, msg["content"]))
            
        messages.append(("user", query))

        # 3. Call LLM (with tools)
        try:
            response_stream = self.llm_with_tools.stream(messages)
            
            # Buffer for tool calls
            final_tool_calls = []
            
            for chunk in response_stream:
                if chunk.tool_calls:
                     final_tool_calls.extend(chunk.tool_calls)
                
                if chunk.content:
                    if isinstance(chunk.content, list):
                        # Join text parts if it's a list (common in some complex LLM outputs)
                        content_str = "".join([c.get("text", str(c)) if isinstance(c, dict) else str(c) for c in chunk.content])
                        yield content_str
                    else:
                        yield str(chunk.content)

            # 4. Handle Tool Execution
            if final_tool_calls:
                 for tool_call in final_tool_calls:
                     if tool_call['name'] == 'create_support_ticket':
                         args = tool_call['args']
                         # Execute tool
                         tool_result = create_support_ticket.invoke(args)
                         yield f"\n\n[System]: {tool_result}"
        except Exception as e:
            yield f"LLM Error: {e}"
