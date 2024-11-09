import streamlit as st
import requests

st.set_page_config(page_title="Email Client", page_icon="📧", layout="centered")

st.title("📧 Email Client")
st.markdown("A simple client for sending and receiving emails.")

with st.sidebar:
    st.header("Actions")
    action = st.radio("Choose an action:", ("Send Email", "Check Inbox"))

if action == "Send Email":
    st.header("📤 Send an Email")
    recipient = st.text_input("Recipient Email", placeholder="Enter recipient's email")
    content = st.text_area("Email Content", placeholder="Write your message here...", height=150)
    
    if st.button("Send Email"):
        with st.spinner("Sending email..."):
            try:
                response = requests.post(
                    "http://localhost:5001/send",
                    json={"recipient": recipient, "content": content}
                )
                response_data = response.json()
                if response_data.get("message") == "Email sent successfully!":
                    st.success("✅ Email sent successfully!")
                else:
                    st.error(f"❌ {response_data.get('error', 'Failed to send email.')}")
            except requests.exceptions.JSONDecodeError:
                st.error("❌ Server did not return a valid JSON response.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to connect to server: {e}")

if action == "Check Inbox":
    st.header("📥 Check Inbox")
    email = st.text_input("Your Email", placeholder="Enter your email address", key="receive_email")
    password = st.text_input("Password", placeholder="Enter your password", type="password", key="receive_password")

    if "email_list" not in st.session_state:
        st.session_state["email_list"] = []

    if st.button("Check Inbox"):
        with st.spinner("Checking inbox..."):
            try:
                response = requests.post(
                    "http://localhost:5001/receive",
                    json={"email": email, "password": password}
                )
                response_data = response.json()
                if "emails" in response_data:
                    st.session_state["email_list"] = response_data["emails"]
                    st.success("📨 Emails retrieved successfully! Select an email to read.")
                else:
                    st.error(f"❌ {response_data.get('error', 'Failed to retrieve emails.')}")
            except requests.exceptions.JSONDecodeError:
                st.error("❌ Server did not return a valid JSON response.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to connect to server: {e}")

    # Display email list with selection and retrieval of content
    if st.session_state["email_list"]:
        st.subheader("📬 Your Email List")
        email_id_to_retrieve = st.selectbox(
            "Select an Email ID to view content",
            options=[email_info["id"] for email_info in st.session_state["email_list"]],
            format_func=lambda x: f"Email ID: {x}"
        )

        email_size = next(
            (email_info["size"] for email_info in st.session_state["email_list"] if email_info["id"] == email_id_to_retrieve),
            None
        )
        st.write(f"**Size:** {email_size} bytes")

        if st.button("Retrieve Selected Email"):
            with st.spinner(f"Retrieving email ID {email_id_to_retrieve}..."):
                try:
                    response = requests.post(
                        f"http://localhost:5001/receive_email/{email_id_to_retrieve}",
                        json={"email": email, "password": password}
                    )
                    email_content_response = response.json()
                    if "content" in email_content_response:
                        st.write(f"**Email Content for ID {email_id_to_retrieve}:**")
                        st.text_area("Email Content", value=email_content_response["content"], height=250, disabled=True)
                    else:
                        st.error(f"❌ {email_content_response.get('error', 'Failed to retrieve email content.')}")
                except requests.exceptions.JSONDecodeError:
                    st.error("❌ Server did not return a valid JSON response.")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Failed to connect to server: {e}")
    else:
        st.info("📭 No emails found. Check your inbox to load emails.")
