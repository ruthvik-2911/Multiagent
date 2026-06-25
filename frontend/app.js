document.addEventListener("DOMContentLoaded", () => {
    
    // --- Navigation Logic ---
    const navItems = document.querySelectorAll(".nav-links li");
    const pages = document.querySelectorAll(".page");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            // Update active nav
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            // Show target page
            const target = item.getAttribute("data-target");
            pages.forEach(p => p.classList.remove("active"));
            document.getElementById(target).classList.add("active");

            // Load data when a specific page is visited
            if (target === "dashboard") loadDashboard();
            if (target === "documents") loadDocuments();
        });
    });

    // --- Dashboard & Documents Logic ---
    async function fetchDocuments() {
        try {
            const res = await fetch("/documents");
            const data = await res.json();
            return data.documents || [];
        } catch (e) {
            console.error("Failed to fetch documents", e);
            return [];
        }
    }

    async function loadDashboard() {
        const docs = await fetchDocuments();
        
        let pdfs = 0, docx = 0, xlsx = 0;
        
        docs.forEach(file => {
            const ext = file.split('.').pop().toLowerCase();
            if (ext === "pdf") pdfs++;
            if (ext === "docx") docx++;
            if (ext === "xlsx" || ext === "xls") xlsx++;
        });

        document.getElementById("total-docs-count").innerText = `${docs.length} Files`;
        document.getElementById("pdf-count").innerText = pdfs;
        document.getElementById("docx-count").innerText = docx;
        document.getElementById("xlsx-count").innerText = xlsx;
    }

    async function loadDocuments() {
        const docsList = document.getElementById("docs-list");
        docsList.innerHTML = `<div class="spinner"></div>`;

        const docs = await fetchDocuments();
        docsList.innerHTML = "";

        if (docs.length === 0) {
            docsList.innerHTML = `<p style="color: var(--text-muted);">No documents indexed yet.</p>`;
            return;
        }

        docs.forEach(file => {
            const ext = file.split('.').pop().toLowerCase();
            let icon = "📄";
            if (ext === "pdf") icon = "📕";
            if (ext === "docx") icon = "📘";
            if (ext === "xlsx" || ext === "xls") icon = "📊";

            const el = document.createElement("div");
            el.className = "doc-item";
            el.innerHTML = `
                <div class="doc-icon">${icon}</div>
                <div class="doc-name">${file}</div>
            `;
            docsList.appendChild(el);
        });
    }

    // --- Upload Logic ---
    const fileInput = document.getElementById("file-upload");
    const dropzone = document.getElementById("dropzone");
    const uploadStatus = document.getElementById("upload-status");
    const uploadSuccess = document.getElementById("upload-success");

    // Click handler for drag and drop visual is handled by label 'for' attribute
    
    // File drop handlers
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });
    
    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });
    
    dropzone.addEventListener("drop", async (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            await handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", async (e) => {
        if (e.target.files.length > 0) {
            await handleFileUpload(e.target.files[0]);
        }
    });

    async function handleFileUpload(file) {
        dropzone.classList.add("hidden");
        uploadStatus.classList.remove("hidden");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                uploadStatus.classList.add("hidden");
                uploadSuccess.classList.remove("hidden");
                
                // Reset after 3 seconds
                setTimeout(() => {
                    uploadSuccess.classList.add("hidden");
                    dropzone.classList.remove("hidden");
                    fileInput.value = "";
                }, 3000);
            } else {
                throw new Error("Server returned " + res.status);
            }
        } catch (e) {
            console.error(e);
            alert("Upload failed.");
            uploadStatus.classList.add("hidden");
            dropzone.classList.remove("hidden");
        }
    }

    // --- Chat Logic ---
    const chatHistory = document.getElementById("chat-history");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    function appendMessage(text, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender}`;
        
        const avatar = sender === "user" ? "👤" : "🤖";
        
        msgDiv.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="bubble">${text}</div>
        `;
        
        chatHistory.appendChild(msgDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    async function sendMessage() {
        const question = chatInput.value.trim();
        if (!question) return;

        appendMessage(question, "user");
        chatInput.value = "";
        
        // Show typing indicator
        const typingId = "typing-" + Date.now();
        const typingDiv = document.createElement("div");
        typingDiv.className = "message assistant";
        typingDiv.id = typingId;
        typingDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble"><div class="spinner" style="width:20px;height:20px;margin:0;border-width:2px;"></div></div>
        `;
        chatHistory.appendChild(typingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question })
            });
            const data = await res.json();
            
            document.getElementById(typingId).remove();
            appendMessage(data.answer, "assistant");
        } catch (e) {
            document.getElementById(typingId).remove();
            appendMessage("Error connecting to server.", "assistant");
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    // Initial Load
    loadDashboard();
});
