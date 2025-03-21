var socket = io(); // Connect to Flask-SocketIO Server

document.addEventListener("DOMContentLoaded", function() {
    const textBox = document.getElementById("text-box");
    const button = document.getElementById("button");

    let selection = ""

    textBox.style.display = "none"; // Hides the text box if click is outside

    document.addEventListener("mouseup", function(event) { 
        checkSelection = window.getSelection().toString().trim(); // Check the current selection

        // If the selection has words and it didnt come from the text box set it to the selection to use
        if (checkSelection.length > 0 && !textBox.contains(event.target)) {
            selection = window.getSelection().toString().trim();
            console.log(selection)

            // set the box at the location
            const range = window.getSelection().getRangeAt(0);
            const rect = range.getBoundingClientRect();

            textBox.style.top = `${rect.bottom + window.scrollY + 5}px`;
            textBox.style.left = `${rect.left + window.scrollX}px`;
            textBox.style.display = "flex";
        }
    });

    /* resize function */
    padding = 0;
    function moveBox(timestamp){
        if (padding < 20){
            padding += .75;
            responseBox.style.padding = padding + "px";
            requestAnimationFrame(moveBox);
        }
      }

    document.addEventListener("mousedown", function(event) {

        if (!textBox.contains(event.target)) {
            textBox.style.display = "none"; // Hides the text box if click is outside
        }

        // if clicked on button
        if (event.target === button) {

            responseBox = document.getElementById("response-text")

            requestAnimationFrame(moveBox); // increase padding

            responseBox.style.display = "block"; // Show the answer field

            


            document.getElementById("input-container").style.padding = "0px 10px 8px 10px"; // change input padding

            // Get the question in input field
            let inputQuestion = document.getElementById("note-input").value;
            console.log(inputQuestion);

            // Send question and selection to backend
       
            console.log(`Button clicked sending ${selection} to GPT`)

            fetch("/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    inputQuestion: inputQuestion,
                    selection: selection
                })
            });
        }
    });

});