import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BuildHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.exe') or event.src_path.endswith('.apk'):
            logging.info(f"New build detected: {event.src_path}")
            self.callback(event.src_path)

class UnityBridge:
    def __init__(self, builds_path: str, notification_callback):
        self.builds_path = builds_path
        self.callback = notification_callback
        self.observer = Observer()

    def start(self):
        if not os.path.exists(self.builds_path):
            os.makedirs(self.builds_path, exist_ok=True)
            
        event_handler = BuildHandler(self.callback)
        self.observer.schedule(event_handler, self.builds_path, recursive=False)
        self.observer.start()
        logging.info(f"UnityBridge started watching {self.builds_path}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
