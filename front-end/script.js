const API_BASE = "http://127.0.0.1:8000";

function getToken() {
    return localStorage.getItem("token");
}

function setToken(token) {
    localStorage.setItem("token", token);
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "index.html";
}

// ================= LOGIN =================
async function loginUser() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: formData
        });

        if (!response.ok) {
            document.getElementById("error").innerText = "Invalid credentials";
            return;
        }

        const data = await response.json();
        setToken(data.access_token);
        window.location.href = "dashboard.html";

    } catch (err) {
        document.getElementById("error").innerText = "Server error";
    }
}

// ================= ADD EXPENSE =================
async function addExpense() {
    const amount = parseFloat(document.getElementById("amount").value);
    const category = document.getElementById("category").value;
    const description = document.getElementById("description").value;

    const response = await fetch(`${API_BASE}/expense`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${getToken()}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            amount,
            category,
            description
        })
    });

    if (response.ok) {
        alert("Expense added");
        loadMonthlySummary();
    } else {
        alert("Failed to add expense");
    }
}

// ================= MONTHLY =================
async function loadMonthlySummary() {
    const year = document.getElementById("year").value;
    const month = document.getElementById("month").value;

    const response = await fetch(
        `${API_BASE}/monthly-summary?year=${year}&month=${month}`,
        {
            headers: {
                "Authorization": `Bearer ${getToken()}`
            }
        }
    );

    if (response.status === 401) {
        logout();
        return;
    }

    const data = await response.json();
    document.getElementById("output").innerText =
        JSON.stringify(data, null, 2);
}

// ================= YEARLY =================
async function loadYearlySummary() {
    const year = document.getElementById("year").value;

    const response = await fetch(
        `${API_BASE}/yearly-summary?year=${year}`,
        {
            headers: {
                "Authorization": `Bearer ${getToken()}`
            }
        }
    );

    const data = await response.json();
    document.getElementById("output").innerText =
        JSON.stringify(data, null, 2);
}

// ================= EXPORT =================
function exportExcel() {
    const year = document.getElementById("year").value;
    const month = document.getElementById("month").value;

    const url =
        `${API_BASE}/export/excel?year=${year}&month=${month}`;

    fetch(url, {
        headers: {
            "Authorization": `Bearer ${getToken()}`
        }
    })
        .then(res => res.blob())
        .then(blob => {
            const link = document.createElement("a");
            link.href = window.URL.createObjectURL(blob);
            link.download = "expenses.xlsx";
            link.click();
        });
}
