document.addEventListener("DOMContentLoaded", function() {
    const textBox = document.getElementById("text-box");
    const boxHeader = document.getElementById("box-header");
    const closeBtn = document.getElementById("close-btn");
    const boxContent = document.getElementById("box-content");
    
    // Show text box only after mouse release
    document.addEventListener("mouseup", function(event) {
    let selection = window.getSelection().toString().trim();

    if (selection.length > 0) {
        console.log("User selected:", selection);
        const range = window.getSelection().getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Position box below the selection
        textBox.style.top = `${rect.bottom + window.scrollY + 10}px`;
        textBox.style.left = `${rect.left + window.scrollX}px`;
        textBox.style.display = "block";

        boxContent.textContent = selection;

        // Autofocus input field
        document.getElementById("note-input").focus();

        fetch("/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ selection: selection })
        });
    }
});
    
    closeBtn.addEventListener("click", function() {
        textBox.style.display = "none";
    });
    
    boxContent.addEventListener("wheel", function(event) {
        event.stopPropagation();
    }, { passive: false });

    let isDragging = false;
    let offsetX, offsetY;
    
    boxHeader.addEventListener("mousedown", function(e) {
        isDragging = true;
        offsetX = e.clientX - textBox.getBoundingClientRect().left;
        offsetY = e.clientY - textBox.getBoundingClientRect().top;
        e.preventDefault();
    });
    
    document.addEventListener("mousemove", function(e) {
        if (isDragging) {
            textBox.style.left = (e.clientX - offsetX) + "px";
            textBox.style.top = (e.clientY - offsetY) + "px";
        }
    });
    
    document.addEventListener("mouseup", function() {
        isDragging = false;
    });
    
    boxContent.addEventListener("mousedown", function(e) {
        e.stopPropagation();
    });
});