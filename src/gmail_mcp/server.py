from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError, ValidationError
import gmail_mcp.gmail.client as gmail_client

gmail_creds = gmail_client.authenticate()

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
    success = gmail_client.remove_label_from_email(gmail_creds, message_id)
    if not success:
        raise ToolError(f"Failed to mark email with ID {message_id} as read.")
    return success

def main():
    """Main function to run the MCP server."""
    print("Starting MCP server...")
    mcp.run()

if __name__ == "__main__":
    main()