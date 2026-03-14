async function checkStatus() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        if (data.status === "ok") {
            const card = document.getElementById("status-card");
            card.classList.add("online");
            document.getElementById("status-text").textContent = "System online";
        }
    } catch (e) {
        document.getElementById("status-text").textContent = "System offline";
    }
}

checkStatus();
