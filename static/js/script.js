const form = document.getElementById("contactForm");
const submitBtn = document.getElementById("submitBtn");
const responseBox = document.getElementById("responseBox");

const fields = {
    name: { input: document.getElementById("name"), error: document.getElementById("nameError"), required: true },
    email: { input: document.getElementById("email"), error: document.getElementById("emailError"), required: true },
    phone: { input: document.getElementById("phone"), error: document.getElementById("phoneError"), required: true },
    message: { input: document.getElementById("message"), error: document.getElementById("messageError"), required: true },
    dob: { input: document.getElementById("dob"), error: document.getElementById("dobError"), required: false },
    gender: { input: document.getElementById("gender"), error: document.getElementById("genderError"), required: false },
    sex: { input: document.getElementById("sex"), error: document.getElementById("sexError"), required: false },
    ethnicity: { input: document.getElementById("ethnicity"), error: document.getElementById("ethnicityError"), required: false },
    disability: { input: document.getElementById("disability"), error: document.getElementById("disabilityError"), required: false },
    maritalStatus: { input: document.getElementById("maritalStatus"), error: document.getElementById("maritalStatusError"), required: false },
    householdSize: { input: document.getElementById("householdSize"), error: document.getElementById("householdSizeError"), required: false },
    familyStructure: { input: document.getElementById("familyStructure"), error: document.getElementById("familyStructureError"), required: false },
    occupation: { input: document.getElementById("occupation"), error: document.getElementById("occupationError"), required: false },
    income: { input: document.getElementById("income"), error: document.getElementById("incomeError"), required: false },
    netWorth: { input: document.getElementById("netWorth"), error: document.getElementById("netWorthError"), required: false },
    language: { input: document.getElementById("language"), error: document.getElementById("languageError"), required: false },
    religion: { input: document.getElementById("religion"), error: document.getElementById("religionError"), required: false },
    geographicLocation: { input: document.getElementById("geographicLocation"), error: document.getElementById("geographicLocationError"), required: false },
    housingTenure: { input: document.getElementById("housingTenure"), error: document.getElementById("housingTenureError"), required: false },
    birthRate: { input: document.getElementById("birthRate"), error: document.getElementById("birthRateError"), required: false },
    deathRate: { input: document.getElementById("deathRate"), error: document.getElementById("deathRateError"), required: false },
    migrationStatus: { input: document.getElementById("migrationStatus"), error: document.getElementById("migrationStatusError"), required: false },
    nationality: { input: document.getElementById("nationality"), error: document.getElementById("nationalityError"), required: true },
    employmentStatus: { input: document.getElementById("employmentStatus"), error: document.getElementById("employmentStatusError"), required: true },
    educationLevel: { input: document.getElementById("educationLevel"), error: document.getElementById("educationLevelError"), required: true },
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^[0-9+\-\s()]{7,20}$/;

function validateField(key) {
    const { input, error, required } = fields[key];
    const value = input.value.trim();
    let message = "";

    if (!value) {
        if (required) message = "This field is required.";
    } else {
        // Specific validations
        if (key === "name" && value.length < 2) {
            message = "Name must be at least 2 characters.";
        } else if (key === "email" && !EMAIL_RE.test(value)) {
            message = "Enter a valid email address.";
        } else if (key === "phone" && !PHONE_RE.test(value)) {
            message = "Enter a valid phone number.";
        } else if (key === "message" && value.length < 5) {
            message = "Message must be at least 5 characters.";
        } else if (key === "nationality" && value.length < 2) {
            message = "Please enter a valid nationality.";
        } else if (key === "householdSize" && (isNaN(value) || parseInt(value) < 0)) {
            message = "Must be a non-negative number.";
        } else if ((key === "income" || key === "netWorth" || key === "birthRate" || key === "deathRate") && isNaN(value)) {
            message = "Must be a number.";
        }
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
        phone: fields.phone.input.value.trim(),
        message: fields.message.input.value.trim(),
        dob: fields.dob.input.value.trim() || null,
        gender: fields.gender.input.value.trim() || null,
        sex: fields.sex.input.value.trim() || null,
        ethnicity: fields.ethnicity.input.value.trim() || null,
        disability: fields.disability.input.value.trim() || null,
        maritalStatus: fields.maritalStatus.input.value.trim() || null,
        householdSize: fields.householdSize.input.value.trim() || null,
        familyStructure: fields.familyStructure.input.value.trim() || null,
        occupation: fields.occupation.input.value.trim() || null,
        income: fields.income.input.value.trim() || null,
        netWorth: fields.netWorth.input.value.trim() || null,
        language: fields.language.input.value.trim() || null,
        religion: fields.religion.input.value.trim() || null,
        geographicLocation: fields.geographicLocation.input.value.trim() || null,
        housingTenure: fields.housingTenure.input.value.trim() || null,
        birthRate: fields.birthRate.input.value.trim() || null,
        deathRate: fields.deathRate.input.value.trim() || null,
        migrationStatus: fields.migrationStatus.input.value.trim() || null,
        nationality: fields.nationality.input.value.trim(),
        employmentStatus: fields.employmentStatus.input.value.trim(),
        educationLevel: fields.educationLevel.input.value.trim(),
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
            showResponse(data.error || "Something went wrong. Please try again.", true);
        }
    } catch (err) {
        showResponse("Network error — could not reach the server.", true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit";
    }
});