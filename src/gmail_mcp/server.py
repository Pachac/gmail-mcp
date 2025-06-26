from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError, ValidationError
import gmail_mcp.gmail.client as gmail_client
import gmail_mcp.cal.client as calendar_client
from gmail_mcp.auth import get_credentials

from datetime import datetime

gmail_creds = get_credentials()

mcp = FastMCP("Gmail MCP Server", "1.0.0")


@mcp.tool()
def get_emails(date_from: str, date_to: str, unread_only: bool = False) -> gmail_client.MessagePreview:
    """Get email previews from Gmail.
    Args:
        date_from (str): The date in YYYY-MM-DD format to filter emails from.
        date_to (str): The date in YYYY-MM-DD format to filter emails to.
        unread_only (bool): Whether to filter for unread emails only.
    Returns:
        List[gmail_client.MessagePreview]: A list of email previews with basic metadata.
    """
    messages = gmail_client.query_emails(gmail_creds, after_date=date_from, before_date=date_to, unread_only=unread_only)
    return messages

@mcp.tool()
def get_labels() -> list[gmail_client.Label]:
    """Get all labels from the Gmail account.
    Returns:
        List[gmail_client.Label]: A list of label objects.
    """
    labels = gmail_client.get_labels(gmail_creds)
    if not labels:
        raise ToolError("No labels found.")
    return labels

@mcp.tool()
def get_email_body(message_id: str) -> str:
    """Get the body of a specific email by its ID.
    Args:
        message_id (str): The ID of the email to retrieve.
    Returns:
        str: The body of the email, or None if not found.
    """
    body = gmail_client.get_email_body(gmail_creds, message_id)
    if body is None:
        raise ToolError(f"Email with ID {message_id} not found.")
    return body

@mcp.tool()
def label_email(message_id: str, label_ids: list) -> bool:
    """Label an email with specified labels.
    Args:
        message_id (str): The ID of the email to label.
        label_ids (list): A list of label IDs to apply to the email.
    Returns:
        bool: True if labeling was successful, False otherwise.
    """
    success = gmail_client.label_email(gmail_creds, message_id, label_ids)
    if not success:
        raise ToolError(f"Failed to label email with ID {message_id}.")
    return success

@mcp.tool()
def mark_email_as_read(message_id: str) -> bool:
    """Mark an email as read by removing the UNREAD label.
    Args:
        message_id (str): The ID of the email to mark as read.
    Returns:
        bool: True if marking as read was successful, False otherwise.
    """
    success = gmail_client.mark_as_read(gmail_creds, message_id)
    if not success:
        raise ToolError(f"Failed to mark email with ID {message_id} as read.")
    return success

@mcp.tool()
def get_calendar_entries_by_date(start_date: str, end_date: str) -> list[calendar_client.CalendarEntry]:
    """Get calendar entries within a specified date range.
    Args:
        start_date (str): The start date in YYYY-MM-DDTHH:MM:SS format.
        end_date (str): The end date in YYYY-MM-DDTHH:MM:SS format.
    Returns:
        List[calendar_client.CalendarEntry]: A list of calendar entries within the specified date range.
    """
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    entries = calendar_client.get_calendar_entries_by_date(gmail_creds, start, end)
    if not entries:
        raise ToolError("No calendar entries found for the specified date range.")
    return entries

@mcp.tool()
def create_calendar_entry(summary: str, start: str, end: str, description: str | None = None, location: str | None = None) -> calendar_client.CalendarEntry:
    """Create a new calendar entry.
    Args:
        summary (str): The summary of the calendar entry.
        start (str): The start date and time in YYYY-MM-DDTHH:MM:SS format.
        end (str): The end date and time in YYYY-MM-DDTHH:MM:SS format.
        description (str | None): Optional description of the calendar entry.
        location (str | None): Optional location of the calendar entry.
    Returns:
        calendar_client.CalendarEntry: The created calendar entry object.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    entry = calendar_client.create_calendar_entry(gmail_creds, calendar_client.CalendryEntryCreate(
        summary=summary,
        start=start_dt,
        end=end_dt,
        description=description,
        location=location
    ))
    return entry

def main():
    """Main function to run the MCP server."""
    print("Starting MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()