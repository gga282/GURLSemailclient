# main.py
import sys
import questionary
from rich.console import Console
from config import login_imap, login_smtp, setting_up_email,login_email
from email_receiver import download_inbox,export_email
import imaplib
import os
from configparser import ConfigParser

def download_inbox_integration():
    """Logs into the IMAP server, retrieves email IDs, and downloads the inbox."""
    base_path = os.getcwd() 
    config_path = os.path.join(base_path, "email.ini")
    from email_receiver import download_inbox

    config = ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        print("Config not found! Please set up email settings")
        setting_up_email()
        config.read(config_path)
    
    host = config.get("imap", "server")
    port = config.getint("imap", "port")
    username = config.get("imap", "username")
    from keyring import get_password
    password = get_password("email_service", username)
    
    try:
        server = imaplib.IMAP4_SSL(host, port, timeout=10)
        server.login(username, password)
        server.select(mailbox="INBOX", readonly=True)
        status, data = server.search(None, "ALL")
        email_ids = data[0].split()
        if email_ids:
            download_inbox(server, email_ids)
        else:
            print("No emails found in inbox.")
        server.logout()
    except Exception as e:
        print(f"Error during download: {e}")

def menu():
    console = Console()
    console.print("[bold blue]Welcome to GURLS - your email client[/bold blue]")
    choice = questionary.select(
        "Please choose an option:",
        choices=[ "Login","Send an email", "Check your inbox", "Set up e-mail account", "Download Inbox","Export email list","Exit"]
    ).ask()

    if choice== "Login":
        login_email()
    elif choice == "Send an email":
        login_smtp()
    elif choice == "Check your inbox":
        login_imap()
    elif choice == "Set up e-mail account":
        setting_up_email()
    elif choice == "Download Inbox":
        download_inbox_integration()
    elif choice == "Export email list":
        export_email()
    #elif choice =="Setting Signature":
    #    input_signature()
    elif choice == "Exit":
        sys.exit(0)

if __name__ == "__main__":
    while True:
        menu()