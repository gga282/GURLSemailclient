# config.py
import os
import keyring
import sys
import smtplib
import imaplib
import questionary
from configparser import ConfigParser
from email_sender import enter_email_address, send_email
from email_receiver import receive_email
import json

CONFIG_FILE="users.json"

def load_ini_to_json(ini_file="email.ini",json_file=CONFIG_FILE):
    """Converts existing ini file to json"""
    if not os.path.exists(ini_file):
        print("No config file found. Please set up an account first.")
        return {}
    
    config=ConfigParser()
    config.read(ini_file)

    data={section:dict(config.items(section)) for section in config.sections()}

    with open(json_file,"w") as f:
        json.dump(data,f,indent=4)

    return data

def login_email():
    """ Checks if the entered username exists, then logs in """
    data = load_ini_to_json()

    if not data:
        setting_up_email()
        return
    u_name=input("Enter username: ")

    stored_username = data.get("imap", {}).get("username", None)

    if stored_username==u_name:
        print("User found! Logging in....")
        login_imap()
    else:
        print("No matching user found. Setting up a new email account.")
        setting_up_email()


def setting_up_email():
    """
    Sets up the email configuration and writes it to a config file.
    """
    
    save_path = os.getcwd()
    config_file = os.path.join(save_path, "email.ini")
    if os.path.exists(config_file):
        print(f"Config file {config_file} already exists")
        return config_file
    username = input("Enter username: ")
    from_addr = input("Enter your email address: ")
    imap_server = input("Enter IMAP email server address: ")
    imap_port = int(input("Enter IMAP port: "))
    smtp_server = input("Enter SMTP email server address: ")
    smtp_port = int(input("Enter SMTP port: "))

    config = ConfigParser()
    config["imap"] = {
        "server": imap_server,
        "username": username,
        "from_addr": from_addr,
        "port": imap_port
    }
    config["smtp"] = {
        "server": smtp_server,
        "username": username,
        "from_addr": from_addr,
        "port": smtp_port
    }

    with open(config_file, "w") as configfile:
        config.write(configfile)

    print(f"Created config file: {config_file}\nSaved!")
    return config_file

def login_imap():
    """
    Logs into the IMAP server using credentials from the config file.
    """
    base_path = os.getcwd()  # Adjust as needed
    config_path = os.path.join(base_path, "email.ini")
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
    password = keyring.get_password("email_service", username)
    server = imaplib.IMAP4_SSL(host, port, timeout=10)
    receive_email(server, username, password)

def login_smtp():
    """
    Logs into the SMTP server and sends an email using credentials from the config file.
    """
    base_path = os.getcwd()  # Adjust as needed
    config_path = os.path.join(base_path, "email.ini")
    config = ConfigParser()

    if os.path.exists(config_path):
        config.read(config_path)
    else:
        print("Config not found! Please set up email settings")
        setting_up_email()
        config.read(config_path)

    to_addr,cc,bcc,subject, body_text, = enter_email_address()
    host = config.get("smtp", "server")
    port = config.getint("smtp", "port")
    username = config.get("smtp", "username")
    password = keyring.get_password("email_service", username)
    from_addr = config.get("smtp", "from_addr")
    server = smtplib.SMTP_SSL(host, port, timeout=10)
    send_email(server, username, password, from_addr, subject, to_addr,cc,bcc, body_text)

def input_signature():
    base_path = os.getcwd()
    with open("signature.html","r",encoding="utf-8") as f:
        signature_html=f.read()
    return signature_html

