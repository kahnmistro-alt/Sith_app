const form = document.getElementById("contactForm");
const submitBtn = document.getElementById("submitBtn");
const responseBox = document.getElementById("responseBox");

const fields = {
    full_name: { input: document.getElementById("full_name"), error: document.getElementById("nameError"), required: true },
    email: { input: document.getElementById("email"), error: document.getElementById("emailError"), required: true },
    id_number: { input: document.getElementById("id_number"), error: document.getElementById("idError"), required: true },
    phone: { input: document.getElementById("phone"), error: document.getElementById("phoneError"), required: false },
    address: { input: document.getElementById("address"), error: document.getElementById("addressError"), required: false },
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^[0-9+\-\s()]{7,20}$/;

function validateField(key) {
    const { input, error, required } = fields[key];
    const value = input.value.trim();
    let message = "";

    if (!value && required) {
        message = "This field is required.";
    } else if (key === "full_name" && value.length < 2) {
        message = "Name must be at least 2 characters.";
    } else if (key === "email" && !EMAIL_RE.test(value)) {
        message = "Enter a valid email address.";
    } else if (key === "id_number" && value.length < 3) {
        message = "ID must be at least 3 characters.";
    } else if (key === "phone" && value && !PHONE_RE.test(value)) {
        message = "Enter a valid phone number.";
    }

    error.textContent = message;
    return message === "";
}

Object.keys(fields).forEach((key) => {
    fields[key].input.addEventListener("blur", () => validateField(key));
    fields[key].input.addEventListener("input", () => {
        if (fields[key].error.textContent) validateField(key);
    });
});

function showResponse(message, isError) {
    responseBox.textContent = message;
    responseBox.classList.remove("hidden", "error-state");
    if (isError) responseBox.classList.add("error-state");
}

form.addEventListener("submit", async(e) => {
    e.preventDefault();

    const validations = Object.keys(fields).map(validateField);
    if (!validations.every(Boolean)) {
        showResponse("Please fix the highlighted fields before submitting.", true);
        return;
    }

    const payload = {
        full_name: fields.full_name.input.value.trim(),
        email: fields.email.input.value.trim(),
        id_number: fields.id_number.input.value.trim(),
        phone: fields.phone.input.value.trim() || null,
        address: fields.address.input.value.trim() || null,
    };

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    try {
        const res = await fetch("/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
            showResponse(data.message || "Submitted successfully.", false);
            form.reset();
        } else {
            showResponse(data.error || "Something went wrong.", true);
        }
    } catch (err) {
        showResponse("Network error — could not reach the server.", true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit";
    }
});