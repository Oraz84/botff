from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import GOOGLE_SERVICE_ACCOUNT, GOOGLE_DRIVE_FOLDER_ID

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = service_account.Credentials.from_service_account_info(GOOGLE_SERVICE_ACCOUNT, scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

def search_files(query: str):
    q = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and fullText contains '{query}'"
    results = drive.files().list(q=q, fields="files(id,name,mimeType)").execute()
    return results.get("files", [])

def download_file(file_id: str):
    request = drive.files().get_media(fileId=file_id)
    return request.execute()
