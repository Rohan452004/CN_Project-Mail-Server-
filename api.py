import logging
from flask import Flask, request, jsonify
import socket

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# SMTP Communication
def send_mail_via_smtp(recipient, content):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(("0.0.0.0", 2525))
            logging.info("Connected to SMTP server")

            welcome_message = client_socket.recv(1024).decode()
            logging.info(f"SMTP server welcome message: {welcome_message}")

            client_socket.sendall(f"HELO localhost\r\n".encode())
            response = client_socket.recv(1024).decode()
            logging.info(f"Response to HELO: {response}")

            client_socket.sendall(f"RCPT TO: {recipient}\r\n".encode())
            response = client_socket.recv(1024).decode()
            logging.info(f"Response to RCPT TO: {response}")

            client_socket.sendall("DATA\r\n".encode())
            response = client_socket.recv(1024).decode()
            logging.info(f"Response to DATA: {response}")

            logging.info(f"Sending email content: {content + '\\r\\n.\\r\\n'}")
            client_socket.sendall((content).encode())
            client_socket.sendall(".\r\n".encode())

            response = client_socket.recv(1024).decode()
            logging.info(f"Response to message content: {response}")

            if "250 Message accepted" in response:
                logging.info("Email sent successfully!")

                client_socket.sendall("QUIT\r\n".encode())
                quit_response = client_socket.recv(1024).decode()
                logging.info(f"Response to QUIT: {quit_response}")

                return "Email sent successfully!"
            else:
                logging.error("Failed to send email.")
                return {"error": "Failed to send email."}
    except Exception as e:
        logging.error(f"SMTP Error: {e}")
        return {"error": str(e)}



# POP3 Communication
def list_emails_via_pop3(email, password):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(("0.0.0.0", 1110))
            welcome_message = client_socket.recv(1024).decode()
            logging.info(f"Connected to POP3 server, received: {welcome_message}")

            client_socket.sendall(f"USER {email}\r\n".encode())
            response = client_socket.recv(1024).decode()
            if "-ERR" in response:
                return {"error": "User not found."}

            client_socket.sendall(f"PASS {password}\r\n".encode())
            response = client_socket.recv(1024).decode()
            if "-ERR" in response:
                return {"error": "Invalid password."}

            client_socket.sendall("LIST\r\n".encode())
            response = client_socket.recv(1024).decode()
            if not response.startswith("+OK"):
                return {"error": "No messages found."}

            emails = [{"id": line.split()[0], "size": line.split()[1]}
                      for line in response.splitlines()[1:-1]]
            logging.info(f"Emails listed: {emails}")
            return {"emails": emails}

    except Exception as e:
        logging.error(f"POP3 Error: {e}")
        return {"error": str(e)}


# POP3 Communication - Retrieve individual email 
def retrieve_email_via_pop3(email, password, email_id):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(("localhost", 1110))
            welcome_message = client_socket.recv(1024).decode()
            logging.info(f"Connected to POP3 server, received: {welcome_message}")

            client_socket.sendall(f"USER {email}\r\n".encode())
            response = client_socket.recv(1024).decode()
            if "-ERR" in response:
                return {"error": "User not found."}

            client_socket.sendall(f"PASS {password}\r\n".encode())
            response = client_socket.recv(1024).decode()
            if "-ERR" in response:
                return {"error": "Invalid password."}

            client_socket.sendall(f"RETR {email_id}\r\n".encode())
            email_response = ""

            while True:
                line = client_socket.recv(1024).decode()
                email_response += line
                logging.info(f"Received line in RETR for email {email_id}: '{line.strip()}'")
                break

            email_lines = email_response.splitlines()
            email_content = "\n".join(email_lines[1:-1]).strip() 

            logging.info(f"Parsed email {email_id} with content: {email_content}")
            return {"id": email_id, "content": email_content}

    except Exception as e:
        logging.error(f"POP3 Error: {e}")
        return {"error": str(e)}


# Send email route
@app.route('/send', methods=['POST'])
def send_email():
    logging.info("Received /send request")
    data = request.json
    recipient = data.get("recipient")
    content = data.get("content")
    result = send_mail_via_smtp(recipient, content)
    logging.info(f"Sending email result: {result}")
    return jsonify({"message": result})

# List emails route
@app.route('/receive', methods=['POST'])
def list_emails():
    logging.info("Received /receive request")
    data = request.json
    email = data.get("email")
    password = data.get("password")
    result = list_emails_via_pop3(email, password)
    logging.info(f"Listing emails result: {result}")
    return jsonify(result)

# Retrieve individual email route
@app.route('/receive_email/<email_id>', methods=['POST'])
def receive_single_email(email_id):
    logging.info(f"Received /receive_email request for email ID {email_id}")
    data = request.json
    email = data.get("email")
    password = data.get("password")
    result = retrieve_email_via_pop3(email, password, email_id)
    logging.info(f"Retrieving email result: {result}")
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5001)
