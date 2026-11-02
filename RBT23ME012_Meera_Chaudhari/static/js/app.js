/**
 * Onyx — Claude-Inspired Career AI Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let currentConversationId = null;
    let currentResumeId = null;
    let currentResumeFilename = null;
    let currentTargetPosition = null;
    let isAnalyzing = false;

    // DOM Elements
    const sidebar = document.getElementById("sidebar");
    const collapseSidebarBtn = document.getElementById("collapseSidebarBtn");
    const expandSidebarBtn = document.getElementById("expandSidebarBtn");
    const newChatBtn = document.getElementById("newChatBtn");
    const historyList = document.getElementById("historyList");
    const activeChatTitle = document.getElementById("activeChatTitle");

    const welcomeScreen = document.getElementById("welcomeScreen");
    const messagesContainer = document.getElementById("messagesContainer");
    const chatViewport = document.getElementById("chatViewport");
    const chatInput = document.getElementById("chatInput");
    const sendBtn = document.getElementById("sendBtn");

    // Badges & Buttons
    const resumeBadge = document.getElementById("resumeBadge");
    const resumeBadgeName = document.getElementById("resumeBadgeName");
    const removeResumeBtn = document.getElementById("removeResumeBtn");
    const positionBadge = document.getElementById("positionBadge");
    const positionBadgeTitle = document.getElementById("positionBadgeTitle");
    const removePositionBtn = document.getElementById("removePositionBtn");

    const triggerUploadBtn = document.getElementById("triggerUploadBtn");
    const resumeFileInput = document.getElementById("resumeFileInput");
    const triggerPositionBtn = document.getElementById("triggerPositionBtn");

    // Modal
    const positionModal = document.getElementById("positionModal");
    const positionInputText = document.getElementById("positionInputText");
    const closePositionModal = document.getElementById("closePositionModal");
    const cancelPositionBtn = document.getElementById("cancelPositionBtn");
    const savePositionBtn = document.getElementById("savePositionBtn");
    const pillHints = document.querySelectorAll(".pill-hint");

    // Starters
    const starterCards = document.querySelectorAll(".starter-card");

    // Initialize Lucide Icons
    function refreshIcons() {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
    refreshIcons();

    // ==========================================
    // Sidebar Collapse / Expand
    // ==========================================
    collapseSidebarBtn.addEventListener("click", () => {
        sidebar.classList.add("collapsed");
        expandSidebarBtn.style.display = "flex";
        refreshIcons();
    });

    expandSidebarBtn.addEventListener("click", () => {
        sidebar.classList.remove("collapsed");
        expandSidebarBtn.style.display = "none";
        refreshIcons();
    });

    // ==========================================
    // Conversation History (Neon DB)
    // ==========================================
    async function loadHistory() {
        try {
            const resp = await fetch("/api/conversations");
            const data = await resp.json();

            historyList.innerHTML = "";
            if (!data || data.length === 0) {
                historyList.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);padding:8px 12px;">No past sessions yet.</div>';
                return;
            }

            data.forEach(item => {
                const div = document.createElement("div");
                div.className = `history-item ${item.id === currentConversationId ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="history-item-content">
                        <i data-lucide="message-square"></i>
                        <span class="history-item-title">${escapeHtml(item.title)}</span>
                    </div>
                    <button class="history-delete-btn" title="Delete" data-id="${item.id}">
                        <i data-lucide="trash-2"></i>
                    </button>
                `;

                div.querySelector(".history-item-content").addEventListener("click", () => {
                    loadConversation(item.id);
                });

                div.querySelector(".history-delete-btn").addEventListener("click", async (e) => {
                    e.stopPropagation();
                    if (confirm("Delete this session from Neon DB?")) {
                        await deleteConversation(item.id);
                    }
                });

                historyList.appendChild(div);
            });
            refreshIcons();
        } catch (e) {
            console.error("Failed to load history:", e);
            historyList.innerHTML = '<div style="font-size:0.8rem;color:var(--danger-text);padding:8px 12px;">Failed to load history.</div>';
        }
    }

    async function loadConversation(id) {
        try {
            const resp = await fetch(`/api/conversations/${id}`);
            if (!resp.ok) return;
            const data = await resp.json();

            currentConversationId = data.id;
            activeChatTitle.textContent = data.title;
            welcomeScreen.style.display = "none";
            messagesContainer.innerHTML = "";

            // Check if resume attached
            if (data.resumes && data.resumes.length > 0) {
                const r = data.resumes[data.resumes.length - 1];
                setResumeBadge(r.id, r.filename);
            } else {
                clearResumeBadge();
            }

            // Restore Messages
            if (data.messages) {
                data.messages.forEach(m => {
                    appendMessageBubble(m.sender, m.content, false);
                });
            }

            // Restore Analysis Cards if any
            if (data.analyses && data.analyses.length > 0) {
                data.analyses.forEach(a => {
                    renderAnalysisCard(a, false);
                });
            }

            loadHistory();
            scrollToBottom();
            refreshIcons();
        } catch (e) {
            console.error("Failed to load conversation:", e);
        }
    }

    async function deleteConversation(id) {
        try {
            await fetch(`/api/conversations/${id}`, { method: "DELETE" });
            if (currentConversationId === id) {
                resetToNewChat();
            } else {
                loadHistory();
            }
        } catch (e) {
            console.error("Failed to delete session:", e);
        }
    }

    function resetToNewChat() {
        currentConversationId = null;
        clearResumeBadge();
        clearPositionBadge();
        activeChatTitle.textContent = "New Career Analysis";
        messagesContainer.innerHTML = "";
        welcomeScreen.style.display = "flex";
        chatInput.value = "";
        loadHistory();
    }

    newChatBtn.addEventListener("click", resetToNewChat);

    // ==========================================
    // Resume Upload Handling
    // ==========================================
    triggerUploadBtn.addEventListener("click", () => {
        resumeFileInput.click();
    });

    resumeFileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        if (currentConversationId) {
            formData.append("conversation_id", currentConversationId);
        }

        triggerUploadBtn.disabled = true;
        triggerUploadBtn.innerHTML = `<div class="spinner-small"></div> <span>Uploading...</span>`;

        try {
            const resp = await fetch("/api/upload-resume", {
                method: "POST",
                body: formData
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert(err.detail || "Upload failed");
                return;
            }

            const data = await resp.json();
            currentConversationId = data.conversation_id;
            setResumeBadge(data.resume_id, data.filename);
            loadHistory();

            // Notify user in chat
            welcomeScreen.style.display = "none";
            appendMessageBubble("gemini", `**Resume attached:** \`${data.filename}\` (${data.char_count} characters extracted). Specify your target position or choose a role to proceed with the analysis.`);
        } catch (err) {
            console.error("Resume upload error:", err);
            alert("Error uploading resume. Check network or file format.");
        } finally {
            triggerUploadBtn.disabled = false;
            triggerUploadBtn.innerHTML = `<i data-lucide="upload"></i> <span>Upload Resume</span>`;
            resumeFileInput.value = "";
            refreshIcons();
        }
    });

    function setResumeBadge(id, filename) {
        currentResumeId = id;
        currentResumeFilename = filename;
        resumeBadgeName.textContent = filename;
        resumeBadge.style.display = "inline-flex";
        refreshIcons();
    }

    function clearResumeBadge() {
        currentResumeId = null;
        currentResumeFilename = null;
        resumeBadge.style.display = "none";
    }

    removeResumeBtn.addEventListener("click", clearResumeBadge);

    // ==========================================
    // Target Position Modal Handling
    // ==========================================
    triggerPositionBtn.addEventListener("click", () => {
        positionModal.style.display = "flex";
        positionInputText.focus();
        refreshIcons();
    });

    closePositionModal.addEventListener("click", () => positionModal.style.display = "none");
    cancelPositionBtn.addEventListener("click", () => positionModal.style.display = "none");

    pillHints.forEach(pill => {
        pill.addEventListener("click", () => {
            positionInputText.value = pill.textContent.trim();
        });
    });

    savePositionBtn.addEventListener("click", () => {
        const val = positionInputText.value.trim();
        if (val) {
            setPositionBadge(val);
            positionModal.style.display = "none";
            positionInputText.value = "";
        }
    });

    function setPositionBadge(positionTitle) {
        currentTargetPosition = positionTitle;
        positionBadgeTitle.textContent = positionTitle;
        positionBadge.style.display = "inline-flex";
        refreshIcons();
    }

    function clearPositionBadge() {
        currentTargetPosition = null;
        positionBadge.style.display = "none";
    }

    removePositionBtn.addEventListener("click", clearPositionBadge);

    // Starter Cards Click
    starterCards.forEach(card => {
        card.addEventListener("click", () => {
            const role = card.getAttribute("data-role");
            setPositionBadge(role);
            if (!currentResumeId) {
                triggerUploadBtn.classList.add("pulse");
                setTimeout(() => triggerUploadBtn.classList.remove("pulse"), 1000);
            }
            chatInput.focus();
        });
    });

    // ==========================================
    // Chat & Analysis Execution
    // ==========================================
    async function handleSubmission() {
        if (isAnalyzing) return;
        const text = chatInput.value.trim();

        // If target position and resume are set, or if user is initiating analysis
        if (currentTargetPosition && currentResumeId && (text === "" || text.toLowerCase().includes("analyze") || text.toLowerCase().includes("match"))) {
            await runAnalysis(currentTargetPosition);
            chatInput.value = "";
            return;
        }

        // If user typed without setting position but resume is there
        if (currentResumeId && !currentTargetPosition && text) {
            // Assume typed text is the position or query
            await runAnalysis(text);
            chatInput.value = "";
            return;
        }

        // Standard conversational chat message
        if (!text) return;
        chatInput.value = "";
        await sendChatMessage(text);
    }

    sendBtn.addEventListener("click", handleSubmission);

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmission();
        }
    });

    async function runAnalysis(position) {
        isAnalyzing = true;
        welcomeScreen.style.display = "none";
        sendBtn.disabled = true;

        appendMessageBubble("user", `Analyze my resume for **${position}** across market sectors.`);
        const loadingId = appendLoadingIndicator("Analyzing job market sectors & evaluating semantic fit...");

        try {
            const resp = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    conversation_id: currentConversationId,
                    resume_id: currentResumeId,
                    target_position: position
                })
            });

            removeLoadingIndicator(loadingId);

            if (!resp.ok) {
                const err = await resp.json();
                appendMessageBubble("gemini", `**Analysis Error:** ${err.detail || "Could not complete analysis."}`);
                return;
            }

            const data = await resp.json();
            currentConversationId = data.conversation_id;
            renderAnalysisCard(data.report, true);
            loadHistory();
        } catch (e) {
            removeLoadingIndicator(loadingId);
            console.error("Analysis failed:", e);
            appendMessageBubble("gemini", `**Network Error:** Could not contact server. Please retry.`);
        } finally {
            isAnalyzing = false;
            sendBtn.disabled = false;
            scrollToBottom();
            refreshIcons();
        }
    }

    async function sendChatMessage(message) {
        isAnalyzing = true;
        welcomeScreen.style.display = "none";
        sendBtn.disabled = true;

        appendMessageBubble("user", message);
        const loadingId = appendLoadingIndicator("Thinking...");

        try {
            // Ensure session exists
            if (!currentConversationId) {
                const initResp = await fetch("/api/conversations", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: message.slice(0, 28) })
                });
                const initData = await initResp.json();
                currentConversationId = initData.id;
            }

            const resp = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    conversation_id: currentConversationId,
                    message: message
                })
            });

            removeLoadingIndicator(loadingId);

            if (!resp.ok) {
                const err = await resp.json();
                appendMessageBubble("gemini", `**Error:** ${err.detail || "Unable to reply."}`);
                return;
            }

            const data = await resp.json();
            appendMessageBubble("gemini", data.response);
            loadHistory();
        } catch (e) {
            removeLoadingIndicator(loadingId);
            console.error("Chat error:", e);
            appendMessageBubble("gemini", `**Network Error:** Could not reach server.`);
        } finally {
            isAnalyzing = false;
            sendBtn.disabled = false;
            scrollToBottom();
            refreshIcons();
        }
    }

    // ==========================================
    // UI Render Helpers
    // ==========================================
    function appendMessageBubble(sender, markdownContent, shouldScroll = true) {
        const row = document.createElement("div");
        row.className = `message-row ${sender}`;

        const parsedHtml = marked.parse(markdownContent || "");

        if (sender === "gemini") {
            row.innerHTML = `
                <div class="message-avatar">
                    <img src="/static/img/logo.png" alt="Onyx">
                </div>
                <div class="message-bubble">${parsedHtml}</div>
            `;
        } else {
            row.innerHTML = `
                <div class="message-bubble">${parsedHtml}</div>
            `;
        }

        messagesContainer.appendChild(row);
        if (shouldScroll) scrollToBottom();
        refreshIcons();
    }

    function renderAnalysisCard(report, shouldScroll = true) {
        const row = document.createElement("div");
        row.className = "message-row gemini";

        // Build Sectors HTML
        let sectorsHtml = "";
        if (report.sectors_data && report.sectors_data.length > 0) {
            sectorsHtml = `
                <div style="font-weight:700;font-size:0.95rem;color:var(--maroon-800);margin-top:14px;">
                    Cross-Sector Industry Fit Analysis
                </div>
                <div class="sectors-grid">
                    ${report.sectors_data.map(s => `
                        <div class="sector-card">
                            <div class="sector-card-header">
                                <span class="sector-name">${escapeHtml(s.sector)}</span>
                                <span class="sector-score">${s.fit_score}%</span>
                            </div>
                            <div class="sector-reqs">${escapeHtml(s.typical_requirements || "")}</div>
                            <div class="sector-notes">${escapeHtml(s.match_notes || "")}</div>
                        </div>
                    `).join("")}
                </div>
            `;
        }

        // Build Strengths HTML
        let strengthsHtml = "";
        if (report.strengths && report.strengths.length > 0) {
            strengthsHtml = `
                <div class="feedback-section strengths">
                    <div class="section-heading"><i data-lucide="check-circle-2"></i> What You Have (Core Strengths)</div>
                    <ul class="feedback-list">
                        ${report.strengths.map(st => `<li>${escapeHtml(st)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        // Build Missing Skills HTML
        let missingHtml = "";
        if (report.missing_skills && report.missing_skills.length > 0) {
            missingHtml = `
                <div class="feedback-section missing">
                    <div class="section-heading"><i data-lucide="alert-triangle"></i> What You Should Add (Market Gaps)</div>
                    <ul class="feedback-list">
                        ${report.missing_skills.map(m => `<li>${escapeHtml(m)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        // Build What to Remove HTML
        let removeHtml = "";
        if (report.what_to_remove && report.what_to_remove.length > 0) {
            removeHtml = `
                <div class="feedback-section remove">
                    <div class="section-heading"><i data-lucide="minus-circle"></i> What You Should Remove / Deprioritize</div>
                    <ul class="feedback-list">
                        ${report.what_to_remove.map(r => `<li>${escapeHtml(r)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        // Build Recommended Bullets HTML
        let bulletsHtml = "";
        if (report.recommended_bullets && report.recommended_bullets.length > 0) {
            bulletsHtml = `
                <div class="feedback-section bullets">
                    <div class="section-heading"><i data-lucide="sparkles"></i> Recommended Resume Bullets to Add</div>
                    <ul class="feedback-list">
                        ${report.recommended_bullets.map(b => `<li><strong>•</strong> ${escapeHtml(b)}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        const summaryHtml = marked.parse(report.summary || report.summary_markdown || "");

        row.innerHTML = `
            <div class="message-avatar">
                <img src="/static/img/logo.png" alt="Onyx">
            </div>
            <div class="message-bubble">
                <div class="analysis-header-card">
                    <div class="analysis-headline">
                        <h2>${escapeHtml(report.target_position)}</h2>
                        <p>${escapeHtml(report.verdict_title || "Market Fit Report")}</p>
                    </div>
                    <div class="score-badge-circle">
                        <span class="score-num">${Math.round(report.overall_score || 0)}%</span>
                        <span class="score-lbl">Fit Score</span>
                    </div>
                </div>

                <div class="analysis-summary">${summaryHtml}</div>
                ${sectorsHtml}
                ${strengthsHtml}
                ${missingHtml}
                ${removeHtml}
                ${bulletsHtml}
            </div>
        `;

        messagesContainer.appendChild(row);
        if (shouldScroll) scrollToBottom();
        refreshIcons();
    }

    function appendLoadingIndicator(text) {
        const id = "loading-" + Date.now();
        const row = document.createElement("div");
        row.className = "message-row gemini";
        row.id = id;
        row.innerHTML = `
            <div class="message-avatar">
                <img src="/static/img/logo.png" alt="Onyx">
            </div>
            <div class="message-bubble" style="display:flex;align-items:center;gap:10px;">
                <div class="spinner-small"></div>
                <span style="font-size:0.88rem;color:var(--text-muted);">${escapeHtml(text)}</span>
            </div>
        `;
        messagesContainer.appendChild(row);
        scrollToBottom();
        return id;
    }

    function removeLoadingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Auto-grow textarea
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + "px";
    });

    // Initial Load
    loadHistory();
});

