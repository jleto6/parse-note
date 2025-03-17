document.addEventListener("DOMContentLoaded", function() {
    const textBox = document.getElementById("text-box");
    const noteInput = document.getElementById("note-input");

    document.addEventListener("mouseup", function(event) {
        let selection = window.getSelection().toString().trim();
        if (selection.length > 0) {
            const range = window.getSelection().getRangeAt(0);
            const rect = range.getBoundingClientRect();

            textBox.style.top = `${rect.bottom + window.scrollY + 5}px`;
            textBox.style.left = `${rect.left + window.scrollX}px`;
            textBox.style.display = "block";

            noteInput.focus();
        }
    });

    document.addEventListener("click", function(event) {
        if (!textBox.contains(event.target)) {
            textBox.style.display = "none";
        }
    });
});