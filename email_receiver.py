#email_receiver.py
import os
import imaplib
import email
import pandas as pd
import questionary
from bs4 import BeautifulSoup
from email_validator import validate_email, EmailNotValidError
from configparser import ConfigParser



def receive_email(server, username, password):
    """
    Logs into the IMAP server, selects the INBOX, and paginates through emails.
    """
     
    try:
        server.login(username, password)
        server.select(mailbox="INBOX", readonly=False)
        status, data = server.search(None, "ALL")
        email_ids = data[0].split()

        if not email_ids:
            print("Inbox is empty.")
            return
        else:
            page_emails(server, email_ids)


    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")



def read_email(server, email_id):
    """
    Fetches and displays a single email by its ID.
    """
    status, email_data = server.fetch(email_id, "(RFC822)")
    raw_email = email_data[0][1]
    msg = email.message_from_bytes(raw_email)
    text_content = ""
    html_content = ""
    
    for part in msg.walk():
        content_type = part.get_content_type()
        if content_type == "text/plain":
            charset = part.get_content_charset() or "utf-8"
            text_content = part.get_payload(decode=True).decode(charset, errors="ignore")
        elif content_type == "text/html":
            charset = part.get_content_charset() or "utf-8"
            html_content = part.get_payload(decode=True).decode(charset, errors="ignore")
        elif part.get_content_disposition() == "attachment":
            attachment_file = part.get_filename()
            file_data = part.get_payload(decode=True)
            download_attachment(attachment_file, file_data)
    
    if html_content:
        clean_text = BeautifulSoup(html_content, "lxml").get_text(separator='\n', strip=True)
        print(clean_text)
    else:
        print(text_content)

def download_attachment(attachment_file, file_data):
    """
    Saves an email attachment to the DownloadedAttachments folder.
    """
    download_folder = os.path.join(os.getcwd(), "DownloadedAttachments")
    os.makedirs(download_folder, exist_ok=True)
    file_path = os.path.join(download_folder, attachment_file)
    with open(file_path, "wb") as fp:
        fp.write(file_data)
    print(f"Saved attachment: {file_path}")

def export_email(server,email_ids):
    """
    Exports email headers (Subject, From, Date) to a CSV file.
    """

    emails = []
    for email_id in email_ids:
        status, email_data = server.fetch(email_id, "(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])")
        raw_email = email_data[0][1].decode("utf-8", errors="ignore").strip()
        msg = email.message_from_string(raw_email)
        emails.append({
            "ID": email_id,
            "Subject": msg.get("Subject", "(No Subject)"),
            "Sender": msg.get("From", "(Unknown Sender)"),
            "Date": msg.get("Date", "(Unknown Date)")
        })
    email_df = pd.DataFrame(emails)
    print(email_df.head())
    email_df.to_csv("emails.csv", index=False)

def page_emails(server, email_ids):
    """
    Paginates through a list of email IDs, allowing the user to select one to read.
    """
    page_size = 10
    current_page = 0
    total_pages = (len(email_ids) - 1) // page_size + 1


    while True:
        start = current_page * page_size
        end = start + page_size
        page_email_ids = email_ids[start:end]
        choices = []
        email_map = {}
        
        for i, email_id in enumerate(page_email_ids, start=1):
            status, email_data = server.fetch(email_id, "(BODY[HEADER.FIELDS (SUBJECT)])")
            subject = email_data[0][1].decode('utf-8', errors='ignore').strip()
            email_label = f"{i}. {subject}"
            choices.append(email_label)
            email_map[email_label] = email_id
        
        if current_page > 0:
            choices.append("<- Previous Page")
        if end < len(email_ids):
            choices.append("-> Next Page")
        choices.append("Exit")

        choice = questionary.select(
            f"Page {current_page + 1}/{total_pages} - Select an email:",
            choices=choices
        ).ask()

        if choice == "-> Next Page":
            current_page += 1
            continue
        elif choice == "<- Previous Page":
            current_page -= 1
            continue
        elif choice == "Exit":
            break
        else:
            selected_email_id = email_map[choice]
            read_email(server, selected_email_id)
            break
    


def search_email(server, search_type, search_value):
    """Searches emails on the server using the given search criteria."""
    status, data = server.search(None, search_type, search_value)
    return data

def search_input(server):
    """Prompts the user for a search criterion and displays matching emails."""
    answer = questionary.select("Search by:",
                                choices=["By Sender", "By Subject", "By Date"]).ask()

    if answer == 'By Sender':
        try:
            by_email = questionary.text("Enter a valid email address: ").ask()
            v=validate_email(by_email)
            email=v["email"]
            data = search_email(server, 'FROM', email)
        except EmailNotValidError as e:
            print("[bold red]Error:[/bold red] Invalid email address.")
    elif answer == 'By Subject':
        by_subject = questionary.text("Enter a word: ").ask()
        data = search_email(server, 'SUBJECT', by_subject)
    elif answer == 'By Date':
        by_date = questionary.text("Enter date (dd-mm-yyyy): ").ask()
        data = search_email(server, 'ON', by_date)
    
    if data and data[0]:
        email_ids = data[0].split()
        for email_id in email_ids:
            read_email(server, email_id)
    else:
        print("No emails found matching the criteria.")

def download_inbox(server, email_ids):
    """
    Downloads all emails from the inbox and saves them as .eml files.
    """
       
    
    export_email(server,email_ids)
    

    save_path = "DownloadedEmails"
    os.makedirs(save_path, exist_ok=True)
    for index, email_id in enumerate(email_ids, start=1):
        email_id = email_id.decode() if isinstance(email_id, bytes) else email_id
        status, email_data = server.fetch(email_id, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch email {email_id}")
            continue
        email_bytes = email_data[0][1]
        file_path = os.path.join(save_path, f'email_{index}.eml')
        with open(file_path, 'wb') as out:
            out.write(email_bytes)
        print(f'Saved: {file_path}')

    
#def get_mailbox():
