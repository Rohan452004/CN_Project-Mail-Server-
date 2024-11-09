import socket
import threading
import os
from threading import Lock
import logging
from datetime import datetime

# logging
logging.basicConfig(level=logging.DEBUG)

# Global Variables
emails = []  
email_mutex = Lock()  
users = {} 

# Functions for File Storage
def load_users_from_file():
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as file:
            for line in file:
                try:
                    email, password = line.strip().split()
                    users[email] = password
                    logging.info(f"Loaded user: {email}")
                except ValueError:
                    logging.warning(f"Skipping malformed line in users.txt: {line}")

def save_user_to_file(email, password):
    with open("users.txt", "a") as file:
        file.write(f"{email} {password}\n")
    logging.info(f"Saved user: {email}")

def save_email_to_file(sender, recipient, content):
    with open("emails.txt", "a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"From: {sender}\nTo: {recipient}\nDate: {timestamp}\n{content}\n---\n")

def load_emails_from_file():
    global emails
    with email_mutex:
        emails.clear() 
        if os.path.exists("emails.txt"):
            with open("emails.txt", "r") as file:
                email = {}
                for line in file:
                    line = line.strip()
                    if line.startswith("From:"):
                        email["sender"] = line[6:].strip()
                    elif line.startswith("To:"):
                        email["recipient"] = line[4:].strip()
                    elif line.startswith("Date:"):
                        email["date"] = line[5:].strip()
                    elif line == "---":
                        if "date" not in email:
                            email["date"] = "Unknown Date"
                        emails.append(email.copy())
                        email.clear()  
                    else:
                        email["content"] = email.get("content", "") + line + "\n"

# SMTP Server
class SMTPServer:
    def start_smtp_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", 2525))
        server_socket.listen(5)
        logging.info("SMTP Server listening on port 2525...")

        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_smtp_client, args=(client_socket,)).start()

    def handle_smtp_client(self, client_socket):
        sender, recipient, data = None, None, None
        try:
            client_socket.sendall(b"220 Welcome to SMTP server\r\n")
            logging.info("SMTP client connected and greeted.")

            while True:
                command = client_socket.recv(1024).decode().strip()
                logging.info(f"Received command: {command}")

                if command.startswith("HELO"):
                    client_socket.sendall(b"250 Hello\r\n")
                    logging.info("Responded to HELO command.")

                elif command.startswith("MAIL FROM"):
                    sender = command[10:].strip()
                    client_socket.sendall(b"250 OK\r\n")
                    logging.info(f"MAIL FROM command received with sender: {sender}")

                elif command.startswith("RCPT TO"):
                    recipient = command[8:].strip()
                    client_socket.sendall(b"250 OK\r\n")
                    logging.info(f"RCPT TO command received with recipient: {recipient}")

                elif command.startswith("DATA"):
                    client_socket.sendall(b"354 End with <CR><LF>.<CR><LF>\r\n")
                    logging.info("DATA command received, waiting for email content.")

                    data = ""
                    while True:
                        line = client_socket.recv(1024).decode()
                        logging.info(f"Received line in DATA: '{line.strip()}'")
                        if line.strip() == ".":
                            logging.info("End of email content (.) detected.")
                            break
                        data += line

                    with email_mutex:
                        emails.append({"sender": sender, "recipient": recipient, "content": data})
                        save_email_to_file(sender, recipient, data)
                    logging.info(f"Email saved from {sender} to {recipient} with content: {data[:50]}...")

                    client_socket.sendall(b"250 Message accepted\r\n")
                    logging.info("Responded with 250 Message accepted.")

                elif command == "QUIT":
                    client_socket.sendall(b"221 Goodbye\r\n")
                    logging.info("QUIT command received, closing connection.")
                    break

                else:
                    client_socket.sendall(b"500 Command not recognized\r\n")
                    logging.warning(f"Unrecognized command received: {command}")

        except (ConnectionResetError, BrokenPipeError):
            logging.error("Client disconnected unexpectedly.")
        finally:
            client_socket.close()
            logging.info("Closed client connection.")

# POP3 Server
class POP3Server:
    def start_pop3_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", 1110))
        server_socket.listen(5)
        logging.info("POP3 Server listening on port 1110...")

        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_pop3_client, args=(client_socket,)).start()

    def handle_pop3_client(self, client_socket):
        current_user = None
        authenticated = False
        try:
            client_socket.sendall(b"+OK POP3 server ready\r\n")

            while True:
                command = client_socket.recv(1024).decode().strip()
                if command.startswith("USER"):
                    current_user = command[5:]
                    if current_user in users:
                        client_socket.sendall(b"+OK User accepted\r\n")
                    else:
                        client_socket.sendall(b"-ERR User not found\r\n")
                elif command.startswith("PASS"):
                    password = command[5:]
                    if users.get(current_user) == password:
                        authenticated = True
                        client_socket.sendall(b"+OK Password accepted\r\n")
                    else:
                        client_socket.sendall(b"-ERR Invalid password\r\n")
                elif command == "LIST" and authenticated:
                    load_emails_from_file()
                    with email_mutex:
                        user_emails = [email for email in emails if email["recipient"] == current_user]
                        response = f"+OK {len(user_emails)} messages\r\n"
                        for i, email in enumerate(user_emails):
                            response += f"{i+1} {len(email['content'])}\r\n"
                        response += ".\r\n"
                        client_socket.sendall(response.encode())
                elif command.startswith("RETR") and authenticated:
                    load_emails_from_file()
                    email_id = int(command.split()[1]) - 1
                    with email_mutex:
                        user_emails = [email for email in emails if email["recipient"] == current_user]
                        if 0 <= email_id < len(user_emails):
                            email = user_emails[email_id]
                            date = email.get("date", "Unknown Date")
                            content = email.get("content", "")
                            response = (
                                f"+OK {len(content)} octets\r\n"
                                f"Date: {date}\r\n"
                                f"{content}\r\n.\r\n"
                            )
                            client_socket.sendall(response.encode())
                        else:
                            client_socket.sendall(b"-ERR No such message\r\n")
                elif command == "QUIT":
                    client_socket.sendall(b"+OK Goodbye\r\n")
                    break
                else:
                    client_socket.sendall(b"-ERR Command not recognized\r\n")

        except (ConnectionResetError, BrokenPipeError):
            logging.error("Client disconnected unexpectedly.")
        finally:
            client_socket.close()
            logging.info("Closed POP3 client connection.")

# Main function to start both SMTP and POP3 servers
if __name__ == "__main__":
    load_users_from_file()
    load_emails_from_file()

    smtp_server = SMTPServer()
    pop3_server = POP3Server()

    smtp_thread = threading.Thread(target=smtp_server.start_smtp_server)
    pop3_thread = threading.Thread(target=pop3_server.start_pop3_server)

    smtp_thread.start()
    pop3_thread.start()

    smtp_thread.join()
    pop3_thread.join()
