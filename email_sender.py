#email_sender.py
import os
import mimetypes
import smtplib
import questionary
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from utils import clear
from rich.console import Console


def enter_email_address():
    """
    Prompts the user for email address, subject, and message body.
    Returns:
        tuple: (receiver_email, subject, body_text)
    """
    receiver_email = input("Please enter email address: ")
    subject = input("Enter Subject: ")
    choice = questionary.select("Do you want add cc ?",
                                choices=["Yes", "No"]).ask()
    if choice=="Yes":
        cc=input("Enter Cc: ")
    else:
        cc=None
    choice=questionary.select("Do you want to add bcc: ",choices=["Yes","No"]).ask()
    if choice=="Yes":
        bcc=input("Enter bcc email address: ")
    else:
        bcc=None
    body_text = input("Please enter your message: ")

    return receiver_email,cc,bcc ,subject, body_text

def add_attachment():
    """
    Handles file attachments for the email.
    Returns:
        tuple: (list of file names, list of MIMEBase attachment parts)
    """
    path = os.path.join(os.getcwd(), 'Attachments')
    os.makedirs(path, exist_ok=True)
    multi_attachment = []
    file_names = []
    
    while True:
        filename = questionary.select("Select a file to attach to the email",
                                      choices=os.listdir(path)).ask()
        file_path = os.path.join(path, filename)
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except IOError as e:
            print(f"Error reading file {filename}: {e}")
            continue
        
        file_names.append(os.path.basename(file_path))
        mimetype_val = mimetypes.guess_type(file_names[-1])[0] or "application/octet-stream"
        main_type, sub_type = mimetype_val.split("/") if "/" in mimetype_val else ("application", "octet-stream")
        attachment_part = MIMEBase(main_type, sub_type)
        attachment_part.set_payload(file_data)
        # Encode attachment in base64
        encoders.encode_base64(attachment_part)
        
        multi_attachment.append(attachment_part)
        
        another_file = questionary.select("Attach another file?",
                                          choices=["Yes", "No"]).ask()
        if another_file == "No":
            break

    return file_names, multi_attachment

def send_email(server, username, password, from_addr, subject, to_addr,cc,bcc, body_text):
    """
    Composes and sends an email using the provided SMTP server.
    """
    console=Console()
    message = MIMEMultipart("mixed")
    message["From"] = from_addr
    message["To"] = to_addr
    message["Cc"]=cc
    message["Bcc"]=bcc
    message["Subject"] = subject
    from config import input_signature
    signature=input_signature()
    part3 = MIMEText(signature,'html')
    

    # Create an inner alternative part for plain text and HTML
    inner_message = MIMEMultipart("alternative")
    key_html = ['<html>', '<body>', '<p>', '<br>', '</p>', '</body>']
    if body_text:
        part1 = MIMEText(body_text, "plain")
        inner_message.attach(part1)
    if any(tag in body_text for tag in key_html):
        part2 = MIMEText(body_text, 'html')
        
        inner_message.attach(part2)
    
    message.attach(inner_message)
    message.attach(part3)
    
    choice = questionary.select("Do you want to add an attachment?",
                                choices=["Yes", "No"]).ask()
    if choice == "Yes":
        file_names, attachment_parts = add_attachment()
        for file_name, attachment_part in zip(file_names, attachment_parts):
            attachment_part.add_header("Content-Disposition", f"attachment; filename={file_name}")
            message.attach(attachment_part)
    
    try:
        server.login(username, password)
        server.sendmail(from_addr, [to_addr], message.as_string())
        server.quit()
        clear()
        console.print(f"[bold green]Email sent to {to_addr} successfully![/bold green]")
    except smtplib.SMTPException as e:
        clear()
        print(f"SMTP error: {e}")