from app import get_notes, update_notes, read_notes
from app import app, update_notes
from threading import Thread
import threading

def run_flask():
    app.run(debug=True, use_reloader=False)  # Starts Flask but doesn't block main.py

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Start the file watcher in a background thread
threading.Thread(target=read_notes, daemon=True).start()

print("Flask is running, but main.py can still execute other code.")