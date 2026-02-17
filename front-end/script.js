const API = "http://127.0.0.1:8000";

function saveToken(token) {
    localStorage.setItem("access_token", token);
}

function getToken() {
    return localStorage.getItem("access_token");
}

function logout() {
    localStorage.removeItem("access_token");
    window.location.href = "index.html";
}

// -------- LOGIN --------
async function loginUser() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
    });

    if (!res.ok) {
        document.getElementById("output").innerText = "Login failed";
        return;
    }

    const data = await res.json();
    saveToken(data.access_token);

    window.location.href = "dashboard.html";
}

// -------- ADD EXPENSE --------
async function addExpense() {
    const token = getToken();
    if (!token) {
        document.getElementById("output").innerText = "Not logged in";
        return;
    }

    const amount = parseFloat(document.getElementById("amount").value);
    const category = document.getElementById("category").value;
    const description = document.getElementById("description").value;

    const res = await fetch(`${API}/expense`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ amount, category, description })
    });

    const data = await res.json();
    document.getElementById("output").innerText = JSON.stringify(data, null, 2);
}

// -------- MONTHLY SUMMARY --------
async function loadMonthlySummary() {
    const token = getToken();
    if (!token) {
        document.getElementById("output").innerText = "Not logged in";
        return;
    }

    const year = document.getElementById("monthYear").value;
    const month = document.getElementById("monthNumber").value;

    const res = await fetch(`${API}/monthly-summary?year=${year}&month=${month}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    document.getElementById("output").innerText = JSON.stringify(data, null, 2);
}

// -------- YEARLY SUMMARY --------
async function loadYearlySummary() {
    const token = getToken();
    if (!token) {
        document.getElementById("output").innerText = "Not logged in";
        return;
    }

    const year = document.getElementById("yearInput").value;

    const res = await fetch(`${API}/yearly-summary?year=${year}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    const data = await res.json();
    document.getElementById("output").innerText = JSON.stringify(data, null, 2);
}

// -------- DOWNLOAD EXCEL (MONTH) --------
function downloadExcelMonth() {
    const token = getToken();
    const year = document.getElementById("monthYear").value;
    const month = document.getElementById("monthNumber").value;

    if (!token) {
        alert("Not logged in!");
        return;
    }
    if (!year || !month) {
        alert("Enter year and month!");
        return;
    }

    fetch(`${API}/export/excel?year=${year}&month=${month}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => {
        if (!res.ok) throw new Error("Download failed");
        return res.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `expenses_${year}_${month}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(err => {
        console.error(err);
        alert("Monthly Excel download failed.");
    });
}

// -------- DOWNLOAD EXCEL (YEAR) --------
function downloadExcelYear() {
    const token = getToken();
    const year = document.getElementById("yearInput").value;

    if (!token) {
        alert("Not logged in!");
        return;
    }
    if (!year) {
        alert("Enter year!");
        return;
    }

    fetch(`${API}/export/excel?year=${year}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    })
    .then(res => {
        if (!res.ok) throw new Error("Download failed");
        return res.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `expenses_${year}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(err => {
        console.error(err);
        alert("Yearly Excel download failed.");
    });
}
