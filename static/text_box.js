var socket = io(); // Connect to Flask-SocketIO Server

document.addEventListener("DOMContentLoaded", function() {
    const textBox = document.getElementById("text-box");
    const button = document.getElementById("send-button");
    const explainButton = document.getElementById("explain-button")

    let range = null;
    let selection = ""

    textBox.style.display = "none"; // Hides the text box if click is outside

    document.addEventListener("mouseup", function(event) { 
        checkSelection = window.getSelection().toString().trim(); // Check the current selection
        sel = window.getSelection

        // If the selection has words and it didnt come from the text box set it to the selection to use
        if (checkSelection.length > 1 && !textBox.contains(event.target)) {
            // Get raw text
            selection = window.getSelection().toString().trim();
            console.log(selection)

            range = window.getSelection().getRangeAt(0);

            // Get HTML text
            const fragment = range.cloneContents();
            const div = document.createElement("div");
            div.appendChild(fragment);

            const serializer = new XMLSerializer();
            rawHTML = serializer.serializeToString(div);
            console.log(rawHTML);

            // set the box at the location
            const rect = range.getBoundingClientRect();

            textBox.style.top = `${rect.bottom + window.scrollY + 5}px`;
            textBox.style.left = `${rect.left + window.scrollX}px`;
            textBox.style.display = "flex";

            // Highlight text
            const highlightSpan = document.createElement("span");
            highlightSpan.style.backgroundColor = "Highlight";
            highlightSpan.classList.add("highlight");

            // Remove any previous highlight
            const previous = document.querySelector("span.highlight");
            if (previous) {
                const parent = previous.parentNode;
                while (previous.firstChild) {
                    parent.insertBefore(previous.firstChild, previous);
                }
                parent.removeChild(previous);
            }

            // Try applying highlight to the new selection
            try {
                const selection = window.getSelection();
                if (!selection.rangeCount) return;

                const range = selection.getRangeAt(0);
                const extracted = range.extractContents();
                highlightSpan.appendChild(extracted);
                range.insertNode(highlightSpan);
            } catch (e) {
                console.error("Unable to highlight selection:", e);
            }
            
        }
    });

    /* resize function */
    padding = 0;
    function moveBox(timestamp){
        if (padding < 20){
            padding += 1;
            responseBox.style.padding = padding + "px";
            requestAnimationFrame(moveBox); 
        }
      }

    document.addEventListener("mousedown", function(event) {
        document.getElementById("file-upload").style.marginTop = "25px"; // move upload box

        if (!textBox.contains(event.target)) {
            textBox.style.display = "none"; // Hides the text box if click is outside
        }
        // if clicked on send button
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
                    type: "question",
                    inputQuestion: inputQuestion,
                    selection: selection
                })
            });
        }

        // if clicked on update explanation
        if (event.target === explainButton) {
            // Send selection to backend
            console.log(`Button clicked sending ${rawHTML} to GPT`)
            fetch("/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    type: "explanation",
                    selection: rawHTML
                })
            });
            // Replace text
            socket.on("explanation", function(data){
                const gptResponse = data.explanation
                const fragment = document.createRange().createContextualFragment(gptResponse);

            range.deleteContents();
            // Insert new GPT content
            range.insertNode(fragment);
        }
    )
        }
    });

});