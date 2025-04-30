import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import get_notes
from app import app
from threading import Thread
import threading

def run_flask():
    app.run(debug=True, use_reloader=False)  # Starts Flask but doesn't block main.py

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

print("Flask is running, but main.py can still execute other code.")