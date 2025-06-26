from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
from pydantic import BaseModel
from datetime import date, timedelta

import base64


class MessagePreview(BaseModel):
    """Model for a message preview."""
    id: str
    subject: str
    sender: str
    preview: str
    received_date: str
    unread: bool = False
    label_ids: list[str] = []  # List of label IDs associated with the message
    

class Label(BaseModel):
    """Model for a Gmail label."""
    id: str
    name: str
    type: str = "user"  # Default type is 'user', can be 'system' or 'label'
    message_list_visibility: str = "show"  # Default visibility is 'show'
    label_list_visibility: str = "labelShow"  # Default label visibility is 'labelShow'


def query_emails(creds, after_date: str, before_date: str, unread_only: bool = False) -> list[MessagePreview]:
    """Query emails using the Gmail API."""
    before_date = (date.fromisoformat(before_date) + timedelta(days=1)).isoformat()
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
            unread=msg["labelIds"] and "UNREAD" in msg["labelIds"],
            label_ids=msg.get("labelIds", []),
        ))
    return previews

def get_email_text(payload):
    """Extract text from the email payload."""
    if payload["mimeType"].startswith("multipart/"):
        return get_email_text(payload["parts"][0])
    elif payload["mimeType"] == "text/html":
        decoded = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        soup = BeautifulSoup(decoded, "html.parser")
        return soup.get_text(strip=True, separator="\n")
    elif payload["mimeType"] == "text/plain":
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    else:
        print(f"Unsupported MIME type: {payload['mimeType']}")
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")


def get_email_body(creds, message_id: str) -> str | None:
    """Get detailed information about a specific email."""
    service = build("gmail", "v1", credentials=creds)
    try:
        message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        return get_email_text(message["payload"])
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
    

def mark_as_read(creds, message_id: str):
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
    


