# Email Client and Server Application

This project is an **Email Client and Server** built using **Python**. It includes both an **SMTP** server for sending emails and a **POP3** server for receiving emails. Additionally, a **Streamlit GUI** acts as the client interface for users to send and retrieve emails conveniently.

## Features

- **SMTP Server**: Handles sending emails from a sender to a recipient.
- **POP3 Server**: Allows users to log in and retrieve emails with timestamps.
- **Streamlit GUI**: User-friendly interface for sending and receiving emails.
- **Real-Time Data Update**: Emails are stored and retrieved with real-time synchronization.
- **File-Based Storage**: Uses simple file storage for users and emails for ease of access.

## Technologies Used

- **Python**: Backend and server-side logic.
- **Streamlit**: GUI framework for the client interface.
- **Sockets**: Network connections for SMTP and POP3 protocols.
- **AWS EC2**: Optional deployment environment.

## Usage

### 1. Send Email
- Go to the "Send Email" section in the GUI.
- Enter the sender email, recipient email, and message content.
- Click **Send Email** to send the message.

### 2. Check Inbox
- Go to the "Receive Emails" section in the GUI.
- Enter your email and password, then click **Check Inbox** to see available emails.
- Select an email ID to view its full content and timestamp.

### 3. Email Storage
- Emails are saved in `emails.txt`, with details like the sender, recipient, date, and content.
- Users are stored in `users.txt`, with email and password information.

## Project Structure

```plaintext
.
├── app.py                  # Streamlit application (client-side GUI)
├── api.py                  # Flask API for handling client requests
├── script.py               # Main script for SMTP and POP3 server logic
├── users.txt               # File storing user credentials
├── emails.txt              # File storing emails
├── requirements.txt        # List of dependencies
└── README.md               # Project documentation


