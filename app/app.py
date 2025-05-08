from flask import Flask, request, render_template
from flask_socketio import SocketIO
from flask import jsonify, Response
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
import re
import markdown
from config import COMPLETED_NOTES, ANSWERS, COMPLETED_NOTES_FILE, NOTE_INPUTS_DIR
from functions.question_manager import question_call

app = Flask(__name__)
app.secret_key = "dev"  # Set a secret key for session
socketio = SocketIO(app)  # Initialize Socket.IO

app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File")
    submit = SubmitField("Upload File")

@app.route("/", methods=["GET", "POST"])
def get_notes():
    form = UploadFileForm()

    # when a POST is recieved 
    if request.method == "POST":
        # File Uploads
        if request.content_type.startswith("multipart/form-data"):
            if form.validate_on_submit():
                file = form.file.data # Grab the file
                file.save(os.path.join(NOTE_INPUTS_DIR, secure_filename(file.filename)))        # JSON Requests
        elif request.content_type == "application/json":
            data = request.get_json()
            action_type = data.get("type")

            if action_type == "question":
                question = data.get("inputQuestion")
                selection = data.get("selection")
                try:
                    for chunk in question_call(question, selection):
                        print(chunk, end="", flush=True)  # Stream to terminal
                    print("")
                except:
                    pass
            # if action_type == "explanation":
            #     selection = data.get("selection")
            #     explanation(selection)

            return "", 204  # Respond with "No Content" since everything happens via socket    
    
    return render_template("index.html", form=form)

# Read from text files on every refresh
@socketio.on('connect')
def handle_connect():

    # Generated Notes
    folder = COMPLETED_NOTES
    files = sorted(os.listdir(folder), key=lambda f: int(re.search(r"\d+", f).group()) if re.search(r"\d+", f) else 0)

    notes_buffer = ""
    for file in files: 
        with open(f"{COMPLETED_NOTES}/{file}", "r") as f:
            stored_notes = f.read()
            stored_notes = markdown.markdown(stored_notes) # Convert to HTML
            notes_buffer += stored_notes

    socketio.emit("update_notes", {"notes": notes_buffer, "refresh": True})

    with open(ANSWERS, "r") as f:
        stored_answers = f.read()
        stored_answers = markdown.markdown(stored_answers) # Convert to HTML
    socketio.emit("answers", {"answer": stored_answers, "refresh": True})

    


