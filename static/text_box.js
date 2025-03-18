document.addEventListener("DOMContentLoaded", function() {
    const textBox = document.getElementById("text-box");
    const button = document.getElementById("button");

    let selection = ""

    textBox.style.display = "none"; // Hides the text box if click is outside

    document.addEventListener("mouseup", function(event) {
        selection = window.getSelection().toString().trim();

        if (selection.length > 0) {
            const range = window.getSelection().getRangeAt(0);
            const rect = range.getBoundingClientRect();

            textBox.style.top = `${rect.bottom + window.scrollY + 5}px`;
            textBox.style.left = `${rect.left + window.scrollX}px`;
            textBox.style.display = "flex";
        }
    });

    document.addEventListener("mousedown", function(event) {

        if (!textBox.contains(event.target)) {
            textBox.style.display = "none"; // Hides the text box if click is outside
        }

        if (event.target === button) {
            console.log(`Button clicked sending ${selection} to GPT`)
        }
    });

});