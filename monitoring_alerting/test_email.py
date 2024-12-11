import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = ""
SENDER_PASSWORD = ""
RECEIVER_EMAIL = "cgordon.dev@gmail.com"

def test_email_connection():
    # Create message
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL
    message["Subject"] = "Test Email from Python Script"
    message.attach(MIMEText("This is a test email.", "plain"))

    try:
        # Create SMTP session
        print("Creating SMTP session...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1)  # Enable debug output
            print("Starting TLS...")
            server.starttls()
            print("Attempting login...")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("Sending email...")
            server.send_message(message)
            print("Email sent successfully!")
            return True
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting email test...")
    test_email_connection()