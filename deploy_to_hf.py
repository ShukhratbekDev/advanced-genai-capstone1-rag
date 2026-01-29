import os
from huggingface_hub import HfApi, create_repo
import glob

# Configuration
SPACE_NAME = "techsolutions-support-rag" # Change this if needed
USERNAME =  input("Enter your HuggingFace Username: ") # e.g. "myusername"
HF_TOKEN = input("Enter your HuggingFace Write Token: ") 

# Files to upload
FILES_TO_UPLOAD = [
    "app.py",
    "rag_engine.py",
    "data_ingestion.py",
    "requirements.txt",
    "data/company_policies.txt",
    "data/library.pdf",
    "data/tutorial.pdf"
]

def deploy():
    api = HfApi(token=HF_TOKEN)
    repo_id = f"{USERNAME}/{SPACE_NAME}"
    
    print(f"Creating Space: {repo_id}...")
    try:
        create_repo(
            repo_id=repo_id,
            token=HF_TOKEN,
            repo_type="space",
            space_sdk="gradio",
            exist_ok=True
        )
        print("Space created successfully (or already exists).")
    except Exception as e:
        print(f"Error creating space: {e}")
        return

    print("Uploading files...")
    for file_path in FILES_TO_UPLOAD:
        if os.path.exists(file_path):
            path_in_repo = file_path # Keep same structure
            print(f"Uploading {file_path}...")
            try:
                api.upload_file(
                    path_or_fileobj=file_path,
                    path_in_repo=path_in_repo,
                    repo_id=repo_id,
                    repo_type="space"
                )
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
        else:
             print(f"Warning: File {file_path} not found locally.")

    print(f"\nDeployment complete! Visit: https://huggingface.co/spaces/{repo_id}")
    print("IMPORTANT: Go to 'Settings' in your Space and add your GOOGLE_API_KEY as a secret.")

if __name__ == "__main__":
    deploy()
