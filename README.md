📂 Google Drive File Manager (CLI-Based)
========================================

A Python-based command-line tool to ****upload****, ****download****, ****browse****, and ****delete**** files/folders on your Google Drive, using your own Google API credentials.

* * *

✅ Features
----------

*   Browse Google Drive folders interactively.
*   Upload local files/folders to any Drive location.
*   Download files/folders with original names.
*   Navigate into Drive folders before downloading or deleting.
*   Delete specific files or folders from Drive.
*   Uses `token.json` for secure OAuth2 authentication.

* * *

🛠️ Setup Instructions
----------------------

### 1\. Enable Google Drive API

1.  Go to Google Cloud Console.
2.  Create a project (or use an existing one).
3.  Enable ****Google Drive API**** for the project.
4.  Go to ****Credentials**** → Create ****OAuth client ID**** → Choose ****Desktop App****.
5.  Download the `credentials.json` file.


### 2\. Project Structure

Place your files like this:

    your_project/
    ├── script.py
    └── tokens/
        └── credentials.json   # ← from Google Cloud Console

🔒 `token.json` will be automatically generated after first successful login.

### 3\. Install Required Libraries

    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

▶️ Running the Script
---------------------

    python script.py

You’ll be prompted with a menu

📌 Notes
--------

*   On first run, your browser will open for Google login and authorization.
*   Your access token will be stored in `tokens/token.json` for future use.
*   All downloads preserve original file/folder names.
*   Folder navigation and actions are recursive and menu-driven.