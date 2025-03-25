# main.py
import os
from colorama import Fore, Style, init
from file_processor import process_single_file
from config import GEMINI_API_KEYS

init(autoreset=True)

def process_folder(folder_path):
    if not GEMINI_API_KEYS:
        print(Fore.RED + "No valid Gemini API keys found!")
        exit(1)

    if not os.path.exists(folder_path):
        print(Fore.RED + f"Folder not found: {folder_path}")
        return

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if file_name.endswith(".txt"):
            process_single_file(file_path)

if __name__ == "__main__":
    chat_folder = "mediafiles/2024/"  # Replace with your folder path
    process_folder(chat_folder)