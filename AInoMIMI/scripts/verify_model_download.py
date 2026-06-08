
import os
from huggingface_hub import hf_hub_url, list_repo_files
import requests

def check_repo(repo_id, filename):
    print(f"Checking {repo_id} for {filename}...")
    try:
        # First, try to list files to see if the file exists (and if repo exists/is public)
        # distinct from just checking if we can download it, this checks directory structure too if needed
        # But simple way is just to construct URL and HEAD it.
        
        url = hf_hub_url(repo_id=repo_id, filename=filename)
        print(f"  URL: {url}")
        
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 200:
            print(f"  [SUCCESS] File found! ({response.headers.get('content-length')} bytes)")
            return True
        elif response.status_code == 302:
             print(f"  [SUCCESS] File found! (Redirect)")
             return True
        else:
            print(f"  [FAILED] Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def main():
    filename = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
    
    candidates = [
        "Eddycrack864/Music-Source-Separation-Training"
    ]
    
    success_repo = None
    
    for repo in candidates:
        if check_repo(repo, filename):
            success_repo = repo
            break
            
    if success_repo:
        print(f"\nFOUND VALID REPOSITORY: {success_repo}")
    else:
        print("\nNO VALID REPOSITORY FOUND.")

if __name__ == "__main__":
    main()
