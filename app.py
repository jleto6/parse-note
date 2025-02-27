from flask import Flask, request, render_template

app = Flask(__name__)

stored_notes = "No notes yet"

@app.route("/")
def get_notes():
    return stored_notes

def update_notes(new_text):
    global stored_notes
    stored_notes = new_text

