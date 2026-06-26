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
        try {
            const hRes = await fetch("/health");
            const health = await hRes.json();
            document.getElementById("h-qdrant").innerText = `🟢 ${health.qdrant}`;
            document.getElementById("h-neo4j").innerText = `🟢 ${health.neo4j}`;
            document.getElementById("h-ollama").innerText = `🟢 ${health.ollama}`;
            document.getElementById("h-planner").innerText = `🟢 ${health.planner}`;
            document.getElementById("h-supervisor").innerText = `🟢 ${health.supervisor}`;
        } catch (e) {}

        try {
            const mRes = await fetch("/metrics");
            const metrics = await mRes.json();
            document.getElementById("m-vectors").innerText = metrics.total_vectors;
            document.getElementById("m-docs").innerText = metrics.total_docs;
            document.getElementById("m-agents").innerText = metrics.agents;
        } catch(e) {}

        const log = document.getElementById("activity-log");
        try {
            const res = await fetch("/activity");
            const activities = await res.json();
            log.innerHTML = "";
            activities.forEach(act => {
                const date = new Date(act.timestamp);
                const timeAgo = Math.floor((Date.now() - date.getTime()) / 1000) + " sec ago";
                log.innerHTML += `
                    <div style="margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <div style="color: #10b981; font-weight: 500;">🟢 ${act.event}</div>
                        <div style="color: var(--text-main); margin-top: 5px;">${act.source}</div>
                        <div style="color: var(--text-muted); font-size: 0.8em; margin-top: 5px;">${timeAgo}</div>
                    </div>
                `;
            });
        } catch (e) {
            log.innerHTML = "<p>Failed to load activity.</p>";
        }
    }

    // --- Enterprise Activity Real-Time SSE ---
    const activityLog = document.getElementById("activity-log");
    if (activityLog) {
        const evtSource = new EventSource("/api/events");
        evtSource.onmessage = function(event) {
            const logEntry = document.createElement("div");
            logEntry.style.marginBottom = "15px";
            logEntry.style.paddingBottom = "10px";
            logEntry.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
            logEntry.innerHTML = `
                <div style="color: #10b981; font-weight: 500;">🟢 ${event.data.replace('🟢 ', '')}</div>
                <div style="color: var(--text-main); margin-top: 5px;">Live Update</div>
                <div style="color: var(--text-muted); font-size: 0.8em; margin-top: 5px;">Just now</div>
            `;
            activityLog.prepend(logEntry);
        };
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

    function appendMessage(text, sender, data = null) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender}`;
        
        const avatar = sender === "user" ? "👤" : "🤖";
        
        let bubbleContent = `<div class="text-content">${text}</div>`;
        
        if (data && data.selected_document) {
            const keywordsHTML = (data.keywords || []).map(k => `<span class="pill" style="display:inline-block; margin:2px; padding:2px 6px; background:rgba(255,255,255,0.1); border-radius:4px; font-size:0.8em;">${k}</span>`).join(" ");
            const confPercent = Math.round(data.confidence * 100);
            bubbleContent += `
                <div class="enterprise-panel" style="margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.9em;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div>
                            <strong style="color:var(--text-light)">Selected Document</strong><br>
                            📄 ${data.selected_document}
                        </div>
                        <div style="text-align: right;">
                            <strong style="color:var(--text-light)">Confidence</strong><br>
                            ${confPercent}%
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong style="color:var(--text-light)">Summary</strong><br>
                        ${data.summary}
                    </div>
                    <div>
                        <strong style="color:var(--text-light)">Keywords</strong><br>
                        ${keywordsHTML}
                    </div>
                </div>
            `;
        }
        
        msgDiv.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="bubble">${bubbleContent}</div>
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
            appendMessage(data.answer, "assistant", data);
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
