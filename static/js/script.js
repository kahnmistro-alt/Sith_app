const form = document.getElementById("profileForm");
const submitBtn = document.getElementById("submitBtn");
const responseBox = document.getElementById("responseBox");

const fields = {
    name: { input: document.getElementById("name"), error: document.getElementById("nameError"), required: true },
    email: { input: document.getElementById("email"), error: document.getElementById("emailError"), required: true },
    phone: { input: document.getElementById("phone"), error: document.getElementById("phoneError"), required: false },
    dob: { input: document.getElementById("dob"), error: document.getElementById("dobError"), required: false },
    gender: { input: document.getElementById("gender"), error: document.getElementById("genderError"), required: false },
    nationality: { input: document.getElementById("nationality"), error: document.getElementById("nationalityError"), required: false },
    message: { input: document.getElementById("message"), error: document.getElementById("messageError"), required: false },
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^[0-9+\-\s()]{7,20}$/;

function validateField(key) {
    const { input, error, required } = fields[key];
    const value = input.value.trim();
    let message = "";

    if (!value && required) {
        message = "This field is required.";
    } else if (key === "name" && value.length < 2) {
        message = "Name must be at least 2 characters.";
    } else if (key === "email" && !EMAIL_RE.test(value)) {
        message = "Enter a valid email address.";
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
        name: fields.name.input.value.trim(),
        email: fields.email.input.value.trim(),
        phone: fields.phone.input.value.trim() || null,
        dob: fields.dob.input.value.trim() || null,
        gender: fields.gender.input.value.trim() || null,
        nationality: fields.nationality.input.value.trim() || null,
        message: fields.message.input.value.trim() || null,
    };

    submitBtn.disabled = true;
    submitBtn.textContent = "Saving...";

    try {
        const res = await fetch("/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (res.ok) {
            showResponse(data.message || "Profile saved successfully.", false);
            form.reset();
        } else {
            showResponse(data.error || "Something went wrong.", true);
        }
    } catch (err) {
        showResponse("Network error — could not reach the server.", true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Save Profile";
    }
});