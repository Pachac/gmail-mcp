import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pydantic import BaseModel

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

class MessagePreview(BaseModel):
    """Model for a message preview."""
    id: str
    subject: str
    sender: str
    preview: str
    received_date: str
    unread: bool = False

class Label(BaseModel):
    """Model for a Gmail label."""
    id: str
    name: str
    type: str = "user"  # Default type is 'user', can be 'system' or 'label'
    message_list_visibility: str = "show"  # Default visibility is 'show'
    label_list_visibility: str = "labelShow"  # Default label visibility is 'labelShow'

def authenticate():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    return creds

def query_emails(creds, after_date: str, before_date: str, unread_only: bool = False):
    """Query emails using the Gmail API."""
    service = build("gmail", "v1", credentials=creds)
    query = f"after:{after_date} before:{before_date}"
    if unread_only:
        query += " is:unread"
    result = service.users().messages().list(userId="me", q=query).execute()
    messages = result.get("messages", [])
    previews = []
    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"], format="metadata", metadataHeaders=["subject", "from", "date"]).execute()
        previews.append(MessagePreview(
            id=msg["id"],
            subject=[header["value"] for header in msg["payload"]["headers"] if header["name"] == "Subject"][0] if any(header["name"] == "Subject" for header in msg["payload"]["headers"]) else "No Subject",
            sender=[header["value"] for header in msg["payload"]["headers"] if header["name"] == "From"][0] if any(header["name"] == "From" for header in msg["payload"]["headers"]) else "Unknown Sender",
            preview=msg["snippet"],
            received_date=[header["value"] for header in msg["payload"]["headers"] if header["name"] == "Date"][0] if any(header["name"] == "Date" for header in msg["payload"]["headers"]) else "Unknown Date",
            unread=msg["labelIds"] and "UNREAD" in msg["labelIds"]
        ))
    return previews

def get_email_body(creds, message_id: str):
    """Get detailed information about a specific email."""
    service = build("gmail", "v1", credentials=creds)
    try:
        message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        return message.get("payload", {}).get("body", {}).get("data", None)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def label_email(creds, message_id: str, label_ids: list):
    """Label an email with specified labels."""
    service = build("gmail", "v1", credentials=creds)
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": label_ids}
        ).execute()
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False

def remove_label_from_email(creds, message_id: str, label_id: str):
    """Remove a specific label from an email."""
    service = build("gmail", "v1", credentials=creds)
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": [label_id]}
        ).execute()
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False
    

def mark_email_as_read(creds, message_id: str):
    """Mark an email as read."""
    return remove_label_from_email(creds, message_id, "UNREAD")

def get_labels(creds):
    """Get all labels in the user's Gmail account."""
    service = build("gmail", "v1", credentials=creds)
    try:
        results = service.users().labels().list(userId="me").execute()
        return [Label(**label) for label in results.get("labels", [])]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    


