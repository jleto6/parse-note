from flask import Flask, request, render_template
from flask_socketio import SocketIO
from flask import jsonify, Response
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
import markdown

from functions.qna import question_call, explanation

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
                file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        # JSON Requests
        elif request.content_type == "application/json":
            data = request.get_json()
            action_type = data.get("type")

            if action_type == "question":
                question = data.get("inputQuestion")
                selection = data.get("selection")
                for chunk in question_call(question, selection):
                    print(chunk, end="", flush=True)  # Stream to terminal
                print("")

            if action_type == "explanation":
                selection = data.get("selection")
                explanation(selection)

            return "", 204  # Respond with "No Content" since everything happens via socket    
    
    return render_template("index.html", form=form)

# Read from notes.txt on every refresh
@socketio.on('connect')
def handle_connect():

    with open("notes.txt", "r") as file:
        stored_notes = file.read()
        stored_notes = markdown.markdown(stored_notes) # Convert to HTML
    socketio.emit("update_notes", {"notes": stored_notes, "refresh": True})

    


