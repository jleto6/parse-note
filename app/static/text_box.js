var socket = io(); // Connect to Flask-SocketIO Server

document.addEventListener("DOMContentLoaded", function() {
    const sidebar = document.querySelector(".sidebar");
    const button = document.getElementById("send-button");
    const explainButton = document.getElementById("explain-button");

    let range = null;
    let selection = "";
    let rawHTML = "";

    document.addEventListener("mouseup", function(event) { 
        checkSelection = window.getSelection().toString().trim(); // Check the current selection
        
        // If the selection has words and it didn't come from the sidebar set it to the selection to use
        if (checkSelection.length > 1 && !sidebar.contains(event.target)) {
            // Get raw text
            selection = window.getSelection().toString().trim();
            console.log(selection);

            range = window.getSelection().getRangeAt(0);

            // Get HTML text
            const fragment = range.cloneContents();
            const div = document.createElement("div");
            div.appendChild(fragment);

            const serializer = new XMLSerializer();
            rawHTML = serializer.serializeToString(div);
            console.log(rawHTML);

            // Highlight text
            const highlightSpan = document.createElement("span");
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

    // Handle send button click
    button.addEventListener("click", function() {
        
        // Get the question in input field
        let inputQuestion = document.getElementById("note-input").value;
        
        if (inputQuestion.trim() === "" && selection.trim() === "") {
            return; // Don't send empty messages
        }
        
        console.log(`Button clicked sending question: ${inputQuestion} and selection: ${selection}`);
        
        // Send question and selection to backend
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
        
        // Clear input after sending
        document.getElementById("note-input").value = "";
    });

    // // Handle explain button click
    // explainButton.addEventListener("click", function() {
    //     if (!rawHTML || rawHTML.trim() === "") {
    //         return; // No selection to explain
    //     }
        
    //     // Send selection to backend
    //     console.log(`Explain button clicked sending: ${rawHTML}`);
    //     fetch("/", {
    //         method: "POST",
    //         headers: {
    //             "Content-Type": "application/json"
    //         },
    //         body: JSON.stringify({
    //             type: "explanation",
    //             selection: rawHTML
    //         })
    //     });
        
    //     // Replace text with explanation when received
    //     socket.on("explanation", function(data) {
    //         if (!range) return;
            
    //         const gptResponse = data.explanation;
    //         const fragment = document.createRange().createContextualFragment(gptResponse);

    //         range.deleteContents();
    //         // Insert new GPT content
    //         range.insertNode(fragment);
    //     });
    // });
    
    // Allow sending with Enter key
    document.getElementById("note-input").addEventListener("keypress", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            button.click();
        }
    });
});