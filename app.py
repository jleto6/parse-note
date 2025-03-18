from flask import Flask, request, render_template
from flask_socketio import SocketIO
from flask import jsonify
import time

from functions.gpt_call import question_call

app = Flask(__name__)
app.secret_key = "dev"  # Set a secret key for session
socketio = SocketIO(app)  # Initialize Socket.IO

stored_notes = "No notes yet"

def read_notes():
    # Continiously check for new notes and emit updates if they change
    last_notes = ""

    while True:
        time.sleep(3)
        if last_notes == "":
            socketio.emit("loading_notes", {"notes" : "Loading Notes..."})

        with open("notes.txt", "r") as file:
            notes = file.read()
            if notes != last_notes:
                new_part = notes.replace(last_notes, "")
                last_notes = notes
                new_part = notes.replace("\n", "<br/>") # Replace new lines with line break element
                #print()
                #print(f"Read notes function: {new_part}")
                socketio.emit("update_notes", {"notes" : new_part})
        time.sleep(1)


@app.route("/", methods=["GET", "POST"])
def get_notes():

    # when a POST is recieved 
    if request.method == "POST":
        question = request.get_json()

        answer = question_call(question)
        print(answer)

        return jsonify(question), 200
    
    # Read from notes.txt on every refresh
    with open("notes.txt", "r") as file:
        stored_notes = file.read()
        stored_notes = stored_notes.replace("\n", "<br/>") # Replace new lines with line break element

    return render_template("index.html", notes=stored_notes)

    


