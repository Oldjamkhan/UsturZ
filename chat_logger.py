import os
import csv
from datetime import datetime

class ChatLogger:
    def __init__(self, log_dir="logs", filename="chat_history.csv"):
        self.log_dir = log_dir
        self.log_file = os.path.join(self.log_dir, filename)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Create file with header if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "User_ID", "Username", "Role", "Message"])

    def log_message(self, user_id, username, role, message_text):
        """
        Logs a message to the CSV file.
        Role can be 'USER' or 'BOT'.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, user_id, username, role, message_text])
        except Exception as e:
            print(f"Logging error: {e}")

    def get_logs_path(self):
        return self.log_file
