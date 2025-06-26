from google.oauth2.credentials import Credentials
import gmail_mcp.config as cfg

def get_credentials():
    return Credentials(
        cfg.TOKEN
        )