import os
import io
import mimetypes
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    creds = None
    # Get the directory where this script resides
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tokens_dir = os.path.join(script_dir, 'tokens')
    token_path = os.path.join(tokens_dir, 'token.json')
    creds_path = os.path.join(tokens_dir, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Ensure the token folder exists
        if not os.path.exists('tokens'):
            os.makedirs('tokens')

        # Save credentials as JSON
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

service = authenticate()

def list_drive_contents(folder_id=None):
    query = f"'{folder_id}' in parents" if folder_id else "'root' in parents"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])

def download_file(file_id, file_name):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    
    request = service.files().get_media(fileId=file_id)
    with open(file_name, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"✅ Downloaded: {file_name}")

def download_folder(folder_id, dest_path):
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    items = list_drive_contents(folder_id)
    for item in items:
        path = os.path.join(dest_path, item['name'])
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            download_folder(item['id'], path)
        else:
            download_file(item['id'], path)

def browse_drive_for_download(folder_id=None, local_base="."):
    while True:
        items = list_drive_contents(folder_id)
        if not items:
            print("🚫 No items found.")
            return

        print(f"\n📁 Drive Contents of folder ID: {folder_id or 'root'}")
        for idx, item in enumerate(items):
            print(f"{idx+1}. {item['name']} ({'Folder' if item['mimeType'] == 'application/vnd.google-apps.folder' else 'File'})")

        choice = input("Select number to proceed or 'b' to go back: ")
        if choice.lower() == 'b':
            return

        try:
            selected = items[int(choice)-1]
            name = selected['name']
            mime = selected['mimeType']
            if mime == 'application/vnd.google-apps.folder':
                action = input(f"'{name}' is a folder. [B]rowse or [D]ownload? ").lower()
                if action == 'b':
                    browse_drive_for_download(selected['id'], os.path.join(local_base, name))
                elif action == 'd':
                    download_folder(selected['id'], os.path.join(local_base, name))
            else:
                download_file(selected['id'], os.path.join(local_base, name))
        except (IndexError, ValueError):
            print("❌ Invalid choice.")

def upload_file(file_path, parent_folder_id=None):
    file_metadata = {'name': os.path.basename(file_path)}
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    media = MediaFileUpload(file_path, resumable=True)
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"📤 Uploaded file: {file_path}")

def upload_folder(folder_path, parent_folder_id=None):
    folder_metadata = {
        'name': os.path.basename(folder_path),
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    folder_id = folder.get('id')
    print(f"📁 Created Drive folder: {folder_path} -> {folder_id}")
    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)
        if os.path.isdir(path):
            upload_folder(path, folder_id)
        else:
            upload_file(path, folder_id)

def browse_local_and_upload(local_path=".", parent_drive_id=None):
    while True:
        entries = sorted(os.listdir(local_path))
        print(f"\n📂 Local Directory: {local_path}")
        for i, entry in enumerate(entries):
            full_path = os.path.join(local_path, entry)
            print(f"{i+1}. {entry} {'[Folder]' if os.path.isdir(full_path) else ''}")

        choice = input("Choose number to upload/browse or 'b' to go back: ")
        if choice.lower() == 'b':
            return
        try:
            selected = entries[int(choice) - 1]
            full_path = os.path.join(local_path, selected)
            if os.path.isdir(full_path):
                action = input(f"'{selected}' is a folder. [B]rowse or [U]pload? ").lower()
                if action == 'b':
                    browse_local_and_upload(full_path, parent_drive_id)
                elif action == 'u':
                    upload_folder(full_path, parent_drive_id)
            else:
                upload_file(full_path, parent_drive_id)
        except (IndexError, ValueError):
            print("❌ Invalid choice.")

def browse_drive_for_delete(folder_id=None):
    while True:
        items = list_drive_contents(folder_id)
        if not items:
            print("🚫 No items to show.")
            return
        print(f"\n🗂️ Drive Folder: {folder_id or 'root'}")
        for i, item in enumerate(items):
            print(f"{i+1}. {item['name']} ({'Folder' if item['mimeType'] == 'application/vnd.google-apps.folder' else 'File'})")

        choice = input("Select number to delete/browse, or 'b' to go back: ")
        if choice.lower() == 'b':
            return
        try:
            selected = items[int(choice) - 1]
            if selected['mimeType'] == 'application/vnd.google-apps.folder':
                action = input(f"'{selected['name']}' is a folder. [B]rowse or [D]elete? ").lower()
                if action == 'b':
                    browse_drive_for_delete(selected['id'])
                elif action == 'd':
                    confirm = input(f"Are you sure you want to delete folder '{selected['name']}'? (y/n): ").lower()
                    if confirm == 'y':
                        service.files().delete(fileId=selected['id']).execute()
                        print("🗑️ Folder deleted.")
            else:
                confirm = input(f"Are you sure you want to delete file '{selected['name']}'? (y/n): ").lower()
                if confirm == 'y':
                    service.files().delete(fileId=selected['id']).execute()
                    print("🗑️ File deleted.")
        except (IndexError, ValueError):
            print("❌ Invalid selection.")

def main_menu():
    while True:
        print("\n========= 📂 Google Drive Manager =========")
        print("1. 📥 Download from Drive")
        print("2. 📤 Upload to Drive")
        print("3. 🗑️ Delete from Drive")
        print("4. ❌ Exit")
        choice = input("Select an option: ")
        if choice == '1':
            base = input("Enter base local download path (default is current directory): ").strip() or "."
            browse_drive_for_download(None, base)
        elif choice == '2':
            base = input("Enter local base folder to browse (default is current directory): ").strip() or "."
            browse_local_and_upload(base)
        elif choice == '3':
            browse_drive_for_delete()
        elif choice == '4':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
