const form = document.getElementById("cvForm");
const submitBtn = document.getElementById("submitBtn");
const responseBox = document.getElementById("responseBox");

const cvInput = document.getElementById("cv_text");
const cvError = document.getElementById("cvError");

function validateCV() {
    const value = cvInput.value.trim();
    if (!value) {
        cvError.textContent = "Please paste your CV content.";
        return false;
    }
    cvError.textContent = "";
    return true;
}

cvInput.addEventListener("blur", validateCV);
cvInput.addEventListener("input", () => {
    if (cvError.textContent) validateCV();
});

function showResponse(message, isError) {
    responseBox.textContent = message;
    responseBox.classList.remove("hidden", "error-state");
    if (isError) responseBox.classList.add("error-state");
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateCV()) {
        showResponse("Please fill in the CV text area.", true);
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    const payload = {
        cv_text: cvInput.value.trim(),
    };

    try {
        const res = await fetch("/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
            showResponse(data.message || "CV submitted successfully.", false);
            form.reset();
        } else {
            showResponse(data.error || "Something went wrong.", true);
        }
    } catch (err) {
        showResponse("Network error — could not reach the server.", true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit CV";
    }
});