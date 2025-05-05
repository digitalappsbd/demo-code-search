#!/usr/bin/env python3
"""
Script to help users set up their Hugging Face token for accessing the Nomic Embed Code model.
"""
import os
import sys
from pathlib import Path
from huggingface_hub import login
from dotenv import load_dotenv, set_key

def main():
    project_root = Path(__file__).resolve().parents[1]
    env_file = os.path.join(project_root, ".env")
    
    print("Nomic Embed Code Authentication Setup")
    print("====================================")
    print(f"This script will help you set up authentication for the Nomic Embed Code model.")
    print(f"You need to create a Hugging Face account and generate an access token.")
    print(f"Visit: https://huggingface.co/settings/tokens to generate a token.\n")
    
    token = input("Enter your Hugging Face token: ").strip()
    
    if not token:
        print("Error: No token provided. Exiting.")
        sys.exit(1)
    
    # Save token to .env file
    if os.path.exists(env_file):
        load_dotenv(env_file)
        set_key(env_file, "HUGGINGFACE_TOKEN", token)
        print(f"Token updated in {env_file}")
    else:
        with open(env_file, "w") as f:
            f.write(f"HUGGINGFACE_TOKEN={token}\n")
        print(f"Token saved to {env_file}")
    
    # Test login
    try:
        print("Testing login to Hugging Face Hub...")
        login(token=token)
        print("Login successful! You can now use the Nomic Embed Code model.")
        print("\nIMPORTANT: Make sure to visit https://huggingface.co/nomic-ai/nomic-embed-code")
        print("and click 'Access repository' to accept the terms and conditions.")
    except Exception as e:
        print(f"Error testing login: {str(e)}")
        print("Please check your token and try again.")
    
if __name__ == "__main__":
    main() 