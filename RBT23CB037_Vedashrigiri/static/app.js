/**
 * ScholarMind.AI — Academic PDF RAG Assistant
 * Frontend Controller: Manages RAG queries, PDF uploads, 3D Flashcards, Exam Quizzes, and Chunk Inspection
 */

document.addEventListener('DOMContentLoaded', () => {
    // State Store
    const state = {
        activeTab: 'chat',
        activeDocId: null,
        activeDocName: '',
        documents: [],
        totalChunks: 0,
        totalPages: 0,
        chatHistory: [],
        flashcards: [],
        currentCardIdx: 0,
        quiz: [],
        currentQuizIdx: 0,
        quizScore: 0,
        quizAnswered: false,
        engineStatus: {},
        allChunks: []
    };

    // DOM Elements
    const elements = {
        // Engine Status
        statusEngineText: document.getElementById('status-engine-text'),
        statusBadge: document.getElementById('engine-status-badge'),
        btnQuickSample: document.getElementById('btn-quick-sample'),
        btnOpenSettings: document.getElementById('btn-open-settings'),

        // Sidebar
        pdfDropzone: document.getElementById('pdf-dropzone'),
        pdfFileInput: document.getElementById('pdf-file-input'),
        btnBrowseFiles: document.getElementById('btn-browse-files'),
        uploadProgressContainer: document.getElementById('upload-progress-container'),
        uploadProgressText: document.getElementById('upload-progress-text'),
        documentListContainer: document.getElementById('document-list-container'),
        btnClearAllDocs: document.getElementById('btn-clear-all-docs'),

        // Stats
        statTotalPages: document.getElementById('stat-total-pages'),
        statTotalChunks: document.getElementById('stat-total-chunks'),
        statReadTime: document.getElementById('stat-read-time'),

        // Mode Navigation Tabs
        tabBtns: document.querySelectorAll('.mode-tab-btn'),
        viewPanels: document.querySelectorAll('.view-panel'),

        // Chat View
        chatWelcomeHero: document.getElementById('chat-welcome-hero'),
        chatMessagesContainer: document.getElementById('chat-messages-container'),
        chatForm: document.getElementById('chat-form'),
        chatUserInput: document.getElementById('chat-user-input'),
        btnSendMessage: document.getElementById('btn-send-message'),
        starterChips: document.querySelectorAll('.query-chip'),

        // Flashcards View
        flashcardElement: document.getElementById('flashcard-element'),
        fcFrontText: document.getElementById('fc-front-text'),
        fcBackText: document.getElementById('fc-back-text'),
        fcCategory: document.getElementById('fc-category'),
        fcPage: document.getElementById('fc-page'),
        fcDoc: document.getElementById('fc-doc'),
        fcCurrentIdx: document.getElementById('fc-current-idx'),
        fcTotalCount: document.getElementById('fc-total-count'),
        btnFcPrev: document.getElementById('btn-fc-prev'),
        btnFcNext: document.getElementById('btn-fc-next'),
        btnFcFlip: document.getElementById('btn-fc-flip'),
        btnRefreshFlashcards: document.getElementById('btn-refresh-flashcards'),

        // Quiz View
        quizQuestionCounter: document.getElementById('quiz-question-counter'),
        quizScoreBadge: document.getElementById('quiz-score-badge'),
        quizProgressFill: document.getElementById('quiz-progress-fill'),
        quizPageCitation: document.getElementById('quiz-page-citation'),
        quizQuestionText: document.getElementById('quiz-question-text'),
        quizOptionsGrid: document.getElementById('quiz-options-grid'),
        quizExplanationBox: document.getElementById('quiz-explanation-box'),
        quizFeedbackIcon: document.getElementById('quiz-feedback-icon'),
        quizFeedbackTitle: document.getElementById('quiz-feedback-title'),
        quizExplanationText: document.getElementById('quiz-explanation-text'),
        btnQuizNext: document.getElementById('btn-quiz-next'),
        btnRefreshQuiz: document.getElementById('btn-refresh-quiz'),

        // Summary View
        summaryOverviewText: document.getElementById('summary-overview-text'),
        summaryFormulasGrid: document.getElementById('summary-formulas-grid'),
        summaryModulesGrid: document.getElementById('summary-modules-grid'),
        btnRefreshSummary: document.getElementById('btn-refresh-summary'),

        // Chunks Explorer View
        chunkSearchInput: document.getElementById('chunk-search-input'),
        chunksCountLabel: document.getElementById('chunks-count-label'),
        chunksResultsGrid: document.getElementById('chunks-results-grid'),

        // Citation Modal
        citationModal: document.getElementById('citation-modal'),
        modalCiteTitle: document.getElementById('modal-cite-title'),
        modalCiteMeta: document.getElementById('modal-cite-meta'),
        modalCiteBadge: document.getElementById('modal-cite-badge'),
        modalCiteSection: document.getElementById('modal-cite-section'),
        modalCiteText: document.getElementById('modal-cite-text'),
        btnCloseCiteModal: document.getElementById('btn-close-cite-modal'),
        btnCiteDone: document.getElementById('btn-cite-done'),

        // Settings Modal
        settingsModal: document.getElementById('settings-modal'),
        settingsApiKey: document.getElementById('settings-api-key'),
        settingsCurrentMode: document.getElementById('settings-current-mode'),
        btnCloseSettingsModal: document.getElementById('btn-close-settings-modal'),
        btnCancelSettings: document.getElementById('btn-cancel-settings'),
        btnSaveSettings: document.getElementById('btn-save-settings')
    };

    // --- Initialization ---
    async function init() {
        setupEventListeners();
        await refreshStatus();
        await refreshDocuments();
    }

    // --- Status & State Sync ---
    async function refreshStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            state.engineStatus = data;
            
            elements.statusEngineText.textContent = data.engine_mode;
            elements.settingsCurrentMode.textContent = data.engine_mode;

            state.totalChunks = data.chunks_count || 0;
            state.totalPages = data.total_pages || 0;

            elements.statTotalChunks.textContent = state.totalChunks;
            elements.statTotalPages.textContent = state.totalPages;
            const readTimeMin = Math.ceil((data.total_words || 0) / 200);
            elements.statReadTime.textContent = `${readTimeMin}m`;
        } catch (e) {
            console.error('Error fetching engine status:', e);
            elements.statusEngineText.textContent = 'Server Disconnected';
        }
    }

    async function refreshDocuments() {
        try {
            const res = await fetch('/api/documents');
            const data = await res.json();
            state.documents = data.documents || [];
            renderDocumentList();
            await refreshStatus();
        } catch (e) {
            console.error('Error fetching documents:', e);
        }
    }

    function renderDocumentList() {
        const container = elements.documentListContainer;
        if (!state.documents || state.documents.length === 0) {
            container.innerHTML = `
                <div class="doc-empty-state">
                    <i class="fa-regular fa-file"></i>
                    <p>No documents uploaded yet.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        state.documents.forEach(doc => {
            const card = document.createElement('div');
            const isActive = state.activeDocId === doc.doc_id;
            card.className = `doc-card ${isActive ? 'active-doc' : ''}`;
            card.style.cursor = 'pointer';
            card.innerHTML = `
                <div class="doc-info" title="Click to focus on ${escapeHtml(doc.filename)}">
                    <i class="fa-solid fa-file-pdf doc-icon"></i>
                    <div class="doc-meta">
                        <span class="doc-name">${escapeHtml(doc.filename)}</span>
                        <div class="doc-badges">
                            <span class="doc-badge">${doc.total_pages} pgs</span>
                            <span class="doc-badge">•</span>
                            <span class="doc-badge">${doc.total_chunks} chunks</span>
                        </div>
                    </div>
                </div>
                <button class="btn-remove-doc" data-id="${doc.doc_id}" title="Remove document">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            `;

            // Clicking card targets this specific document
            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-remove-doc')) return;
                state.activeDocId = doc.doc_id;
                state.activeDocName = doc.filename;
                state.flashcards = [];
                state.quiz = [];
                renderDocumentList();
                showNotification(`Active study focus set to: "${doc.filename}"`);
            });

            container.appendChild(card);
        });

        // Add event listeners for removal
        container.querySelectorAll('.btn-remove-doc').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const docId = btn.getAttribute('data-id');
                if (state.activeDocId === docId) {
                    state.activeDocId = null;
                    state.activeDocName = '';
                }
                await deleteDocument(docId);
            });
        });
    }

    async function deleteDocument(docId) {
        try {
            await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
            state.flashcards = [];
            state.quiz = [];
            await refreshDocuments();
            showNotification('Document removed from RAG index.');
        } catch (e) {
            console.error('Failed to delete doc:', e);
        }
    }

    // --- Tab Switching ---
    function switchTab(tabName) {
        state.activeTab = tabName;

        elements.tabBtns.forEach(btn => {
            if (btn.getAttribute('data-tab') === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        elements.viewPanels.forEach(panel => {
            if (panel.id === `view-${tabName}`) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });

        // Lazy load tab data
        if (tabName === 'flashcards' && state.flashcards.length === 0) {
            loadFlashcards();
        } else if (tabName === 'quiz' && state.quiz.length === 0) {
            loadQuiz();
        } else if (tabName === 'summary') {
            loadSummary();
        } else if (tabName === 'chunks') {
            loadChunks();
        }
    }

    // --- File Uploading & Sample Notes ---
    async function uploadFiles(files) {
        if (!files || files.length === 0) return;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        elements.uploadProgressContainer.classList.remove('hidden');
        elements.uploadProgressText.textContent = `Uploading and indexing ${files.length} PDF(s)...`;

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            elements.uploadProgressContainer.classList.add('hidden');

            if (data.uploaded && data.uploaded.length > 0) {
                const latestDoc = data.uploaded[data.uploaded.length - 1];
                state.activeDocId = data.latest_doc_id || latestDoc.doc_id;
                state.activeDocName = latestDoc.filename;

                // Reset flashcards and quiz so they regenerate specifically from this uploaded file
                state.flashcards = [];
                state.quiz = [];

                await refreshDocuments();

                // 1. Immediately switch to the Academic Chat tab
                switchTab('chat');
                elements.chatWelcomeHero.style.display = 'none';

                // 2. Render an informative Upload Success Banner in the chat
                const banner = document.createElement('div');
                banner.className = 'upload-success-banner';
                banner.innerHTML = `
                    <div class="upload-banner-header">
                        <i class="fa-solid fa-file-circle-check"></i>
                        <div>
                            <h4>Document Indexed: ${escapeHtml(latestDoc.filename)}</h4>
                            <p>Extracted ${latestDoc.total_pages} page(s) and indexed ${latestDoc.total_chunks} semantic chunks. You can now ask questions strictly based on this uploaded content!</p>
                        </div>
                    </div>
                `;

                // 3. Render questions extracted directly from the uploaded PDF
                if (data.suggested_questions && data.suggested_questions.length > 0) {
                    const qBox = document.createElement('div');
                    qBox.className = 'uploaded-questions-box';
                    qBox.innerHTML = `<span class="box-title"><i class="fa-solid fa-lightbulb"></i> Suggested Questions from "${escapeHtml(latestDoc.filename)}":</span>`;
                    const pillsGrid = document.createElement('div');
                    pillsGrid.className = 'uploaded-pills-grid';
                    data.suggested_questions.forEach(q => {
                        const chip = document.createElement('button');
                        chip.className = 'query-chip';
                        chip.innerHTML = `<i class="fa-solid fa-arrow-right"></i> ${escapeHtml(q)}`;
                        chip.addEventListener('click', () => {
                            elements.chatUserInput.value = q;
                            handleChatSubmit();
                        });
                        pillsGrid.appendChild(chip);
                    });
                    qBox.appendChild(pillsGrid);
                    banner.appendChild(qBox);
                }

                elements.chatMessagesContainer.appendChild(banner);
                elements.chatMessagesContainer.scrollTop = elements.chatMessagesContainer.scrollHeight;
                elements.chatUserInput.focus();

                showNotification(`Successfully indexed "${latestDoc.filename}"! Ready to ask questions.`);
            }

            if (data.errors && data.errors.length > 0) {
                alert(`Upload warning: ${data.errors.join(', ')}`);
            }
        } catch (e) {
            console.error('Upload failed:', e);
            elements.uploadProgressContainer.classList.add('hidden');
            alert('Upload failed: ' + e.message);
        }
    }

    async function loadSampleNotes() {
        elements.btnQuickSample.disabled = true;
        elements.btnQuickSample.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading...';

        try {
            const res = await fetch('/api/load-sample', { method: 'POST' });
            const data = await res.json();
            state.activeDocId = data.latest_doc_id;
            state.activeDocName = 'Sample Academic Notes';
            state.flashcards = [];
            state.quiz = [];
            showNotification(data.message || 'Sample notes loaded successfully!');
            await refreshDocuments();
            switchTab('chat');
        } catch (e) {
            console.error('Failed to load sample notes:', e);
        } finally {
            elements.btnQuickSample.disabled = false;
            elements.btnQuickSample.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Load Sample Notes';
        }
    }

    async function clearAllDocuments() {
        if (!confirm('Are you sure you want to clear all indexed academic documents?')) return;
        try {
            await fetch('/api/clear', { method: 'DELETE' });
            state.documents = [];
            state.flashcards = [];
            state.quiz = [];
            state.chatHistory = [];
            elements.chatMessagesContainer.innerHTML = '';
            elements.chatWelcomeHero.style.display = 'flex';
            await refreshDocuments();
            showNotification('Cleared all documents and reset index.');
        } catch (e) {
            console.error('Failed to clear documents:', e);
        }
    }

    // --- Chat Interface ---
    async function handleChatSubmit(e) {
        if (e) e.preventDefault();
        const query = elements.chatUserInput.value.trim();
        if (!query) return;

        // Hide welcome hero on first message
        elements.chatWelcomeHero.style.display = 'none';

        // Append user message
        appendUserMessage(query);
        elements.chatUserInput.value = '';
        autoResizeTextarea(elements.chatUserInput);

        // Show typing indicator
        const typingEl = appendTypingIndicator();
        elements.chatMessagesContainer.scrollTop = elements.chatMessagesContainer.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: query,
                    history: state.chatHistory.map(h => ({ role: h.role, content: h.content }))
                })
            });

            const data = await res.json();
            typingEl.remove();

            // Store history
            state.chatHistory.push({ role: 'user', content: query });
            state.chatHistory.push({ role: 'assistant', content: data.answer });

            appendBotMessage(data);
        } catch (err) {
            typingEl.remove();
            appendBotMessage({
                answer: '❌ Error communicating with the RAG engine: ' + err.message,
                citations: [],
                confidence: 0,
                follow_up_questions: []
            });
        }

        elements.chatMessagesContainer.scrollTop = elements.chatMessagesContainer.scrollHeight;
    }

    function appendUserMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'message-bubble user-message';
        msg.innerHTML = `
            <div class="message-avatar user-avatar">
                <i class="fa-solid fa-user-graduate"></i>
            </div>
            <div class="message-content-wrapper">
                <div class="message-bubble-content">${escapeHtml(text)}</div>
            </div>
        `;
        elements.chatMessagesContainer.appendChild(msg);
    }

    function appendTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'message-bubble bot-message typing-indicator-bubble';
        typing.innerHTML = `
            <div class="message-avatar bot-avatar">
                <i class="fa-solid fa-brain"></i>
            </div>
            <div class="message-content-wrapper">
                <div class="message-bubble-content">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 0.5rem;">
                        Searching chunks & synthesizing grounded response...
                    </span>
                </div>
            </div>
        `;
        elements.chatMessagesContainer.appendChild(typing);
        return typing;
    }

    function appendBotMessage(data) {
        const msg = document.createElement('div');
        msg.className = 'message-bubble bot-message';

        // Render Citations
        let citationsHtml = '';
        if (data.citations && data.citations.length > 0) {
            citationsHtml = '<div class="citations-bar">';
            citationsHtml += `<span class="confidence-badge"><i class="fa-solid fa-shield-check"></i> ${Math.round((data.confidence || 0.9) * 100)}% Grounded</span>`;
            data.citations.forEach((c, idx) => {
                citationsHtml += `
                    <button class="citation-chip" data-idx="${idx}">
                        <i class="fa-solid fa-file-lines"></i>
                        <span>${escapeHtml(c.doc_name)} (p.${c.page})</span>
                        <span style="opacity: 0.7;">• ${c.relevance}%</span>
                    </button>
                `;
            });
            citationsHtml += '</div>';
        }

        // Render Follow-ups
        let followupsHtml = '';
        if (data.follow_up_questions && data.follow_up_questions.length > 0) {
            followupsHtml = '<div class="followups-container">';
            followupsHtml += '<span class="followups-label"><i class="fa-solid fa-lightbulb"></i> Recommended Study Questions:</span>';
            followupsHtml += '<div class="followup-pills">';
            data.follow_up_questions.forEach(q => {
                followupsHtml += `<button class="followup-pill" data-query="${escapeHtml(q)}">${escapeHtml(q)}</button>`;
            });
            followupsHtml += '</div></div>';
        }

        const formattedAnswer = formatMarkdown(data.answer);

        msg.innerHTML = `
            <div class="message-avatar bot-avatar">
                <i class="fa-solid fa-brain"></i>
            </div>
            <div class="message-content-wrapper">
                <div class="message-bubble-content">${formattedAnswer}</div>
                ${citationsHtml}
                ${followupsHtml}
            </div>
        `;

        elements.chatMessagesContainer.appendChild(msg);

        // Bind citation chips
        if (data.citations) {
            msg.querySelectorAll('.citation-chip').forEach(chip => {
                chip.addEventListener('click', () => {
                    const idx = parseInt(chip.getAttribute('data-idx'), 10);
                    openCitationModal(data.citations[idx]);
                });
            });
        }

        // Bind follow-up pills
        msg.querySelectorAll('.followup-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const query = pill.getAttribute('data-query');
                elements.chatUserInput.value = query;
                handleChatSubmit();
            });
        });
    }

    function openCitationModal(citation) {
        elements.modalCiteTitle.textContent = `Citation from ${citation.doc_name}`;
        elements.modalCiteMeta.textContent = `Document: ${citation.doc_name} | Page: ${citation.page}`;
        elements.modalCiteBadge.textContent = `Relevance Score: ${citation.relevance}%`;
        elements.modalCiteSection.textContent = citation.section || `Page ${citation.page}`;
        elements.modalCiteText.textContent = citation.snippet || 'No text snippet available.';
        elements.citationModal.classList.remove('hidden');
    }

    // --- Flashcards Mode ---
    async function loadFlashcards() {
        elements.fcFrontText.textContent = state.activeDocName 
            ? `Extracting key terms from "${state.activeDocName}"...`
            : 'Extracting key terms and generating flashcards...';
        elements.fcBackText.textContent = '';
        try {
            const url = state.activeDocId ? `/api/flashcards?doc_id=${encodeURIComponent(state.activeDocId)}` : '/api/flashcards';
            const res = await fetch(url, { method: 'POST' });
            const data = await res.json();
            state.flashcards = data.flashcards || [];
            state.currentCardIdx = 0;
            renderFlashcard();
        } catch (e) {
            console.error('Failed to load flashcards:', e);
            elements.fcFrontText.textContent = 'Upload PDF notes to generate study flashcards.';
        }
    }

    function renderFlashcard() {
        if (!state.flashcards || state.flashcards.length === 0) {
            elements.fcFrontText.textContent = 'No flashcards generated yet. Upload academic notes to begin.';
            elements.fcBackText.textContent = '';
            elements.fcTotalCount.textContent = '0';
            elements.fcCurrentIdx.textContent = '0';
            return;
        }

        const card = state.flashcards[state.currentCardIdx];
        elements.flashcardElement.classList.remove('flipped');

        elements.fcFrontText.textContent = card.front;
        elements.fcBackText.textContent = card.back;
        elements.fcCategory.textContent = card.category || 'Concept';
        elements.fcPage.textContent = `Page ${card.page || 1}`;
        elements.fcDoc.textContent = card.doc_name || 'Academic Notes';

        elements.fcCurrentIdx.textContent = state.currentCardIdx + 1;
        elements.fcTotalCount.textContent = state.flashcards.length;
    }

    function flipFlashcard() {
        elements.flashcardElement.classList.toggle('flipped');
    }

    function prevFlashcard() {
        if (state.flashcards.length === 0) return;
        state.currentCardIdx = (state.currentCardIdx - 1 + state.flashcards.length) % state.flashcards.length;
        renderFlashcard();
    }

    function nextFlashcard() {
        if (state.flashcards.length === 0) return;
        state.currentCardIdx = (state.currentCardIdx + 1) % state.flashcards.length;
        renderFlashcard();
    }

    // --- Practice Exam Quiz Mode ---
    async function loadQuiz() {
        const docTitle = state.activeDocName ? ` from "${state.activeDocName}"` : '';
        elements.quizQuestionText.textContent = `Synthesizing practice exam questions${docTitle}...`;
        elements.quizOptionsGrid.innerHTML = '';
        elements.quizExplanationBox.classList.add('hidden');
        elements.btnQuizNext.classList.add('hidden');

        const subEl = document.querySelector('#view-quiz .panel-subtitle');
        if (subEl) {
            subEl.textContent = state.activeDocName
                ? `Questions generated strictly from your uploaded note: "${state.activeDocName}".`
                : 'Test your retention with exam-style questions generated strictly from your notes.';
        }

        try {
            const url = state.activeDocId ? `/api/quiz?doc_id=${encodeURIComponent(state.activeDocId)}` : '/api/quiz';
            const res = await fetch(url, { method: 'POST' });
            const data = await res.json();
            state.quiz = data.quiz || [];
            state.currentQuizIdx = 0;
            state.quizScore = 0;
            renderQuizQuestion();
        } catch (e) {
            console.error('Failed to load quiz:', e);
            elements.quizQuestionText.textContent = 'Upload PDF notes to generate a practice exam quiz.';
        }
    }

    function renderQuizQuestion() {
        if (!state.quiz || state.quiz.length === 0) {
            elements.quizQuestionText.textContent = 'No quiz questions available. Upload academic notes to generate an exam prep quiz.';
            elements.quizOptionsGrid.innerHTML = '';
            return;
        }

        state.quizAnswered = false;
        const q = state.quiz[state.currentQuizIdx];
        const total = state.quiz.length;

        elements.quizQuestionCounter.textContent = `Question ${state.currentQuizIdx + 1} of ${total}`;
        elements.quizScoreBadge.textContent = `Score: ${state.quizScore} / ${state.currentQuizIdx}`;
        elements.quizProgressFill.style.width = `${((state.currentQuizIdx + 1) / total) * 100}%`;

        elements.quizPageCitation.textContent = `Cited from Page ${q.page || 1}`;
        elements.quizQuestionText.textContent = q.question;

        elements.quizExplanationBox.classList.add('hidden');
        elements.btnQuizNext.classList.add('hidden');

        const letters = ['A', 'B', 'C', 'D'];
        elements.quizOptionsGrid.innerHTML = '';

        q.options.forEach((opt, idx) => {
            const btn = document.createElement('button');
            btn.className = 'quiz-option-btn';
            btn.innerHTML = `
                <span class="quiz-option-letter">${letters[idx]}</span>
                <span class="quiz-option-text">${escapeHtml(opt)}</span>
            `;
            btn.addEventListener('click', () => handleQuizAnswer(idx, btn));
            elements.quizOptionsGrid.appendChild(btn);
        });
    }

    function handleQuizAnswer(selectedIndex, clickedBtn) {
        if (state.quizAnswered) return;
        state.quizAnswered = true;

        const q = state.quiz[state.currentQuizIdx];
        const correctIndex = q.correct_index;
        const isCorrect = selectedIndex === correctIndex;

        if (isCorrect) {
            state.quizScore++;
            clickedBtn.classList.add('correct');
            elements.quizFeedbackTitle.textContent = 'Correct!';
            elements.quizFeedbackTitle.className = 'explanation-header correct';
            elements.quizFeedbackIcon.className = 'fa-solid fa-circle-check';
        } else {
            clickedBtn.classList.add('incorrect');
            elements.quizFeedbackTitle.textContent = 'Incorrect';
            elements.quizFeedbackTitle.className = 'explanation-header incorrect';
            elements.quizFeedbackIcon.className = 'fa-solid fa-circle-xmark';

            // Highlight the true correct option
            const allBtns = elements.quizOptionsGrid.querySelectorAll('.quiz-option-btn');
            if (allBtns[correctIndex]) {
                allBtns[correctIndex].classList.add('correct');
            }
        }

        elements.quizScoreBadge.textContent = `Score: ${state.quizScore} / ${state.currentQuizIdx + 1}`;
        elements.quizExplanationText.textContent = q.explanation;
        elements.quizExplanationBox.classList.remove('hidden');

        elements.btnQuizNext.classList.remove('hidden');
        if (state.currentQuizIdx === state.quiz.length - 1) {
            elements.btnQuizNext.innerHTML = 'Finish Exam Quiz <i class="fa-solid fa-flag-checkered"></i>';
        } else {
            elements.btnQuizNext.innerHTML = 'Next Question <i class="fa-solid fa-arrow-right"></i>';
        }
    }

    function nextQuizQuestion() {
        if (state.currentQuizIdx < state.quiz.length - 1) {
            state.currentQuizIdx++;
            renderQuizQuestion();
        } else {
            // Quiz completed
            const total = state.quiz.length;
            const percentage = Math.round((state.quizScore / total) * 100);
            elements.quizQuestionText.innerHTML = `
                🎉 Practice Exam Complete!<br/>
                <span style="color: var(--accent-cyan); font-size: 1.5rem;">
                    You scored ${state.quizScore} out of ${total} (${percentage}%)
                </span>
            `;
            elements.quizOptionsGrid.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                        ${percentage >= 80 ? 'Outstanding mastery of the lecture materials!' : 'Good effort! Review the flashcards and executive summary to reinforce weaker areas.'}
                    </p>
                    <button id="btn-restart-quiz" class="btn btn-primary">Retake Exam Quiz</button>
                </div>
            `;
            elements.quizExplanationBox.classList.add('hidden');
            elements.btnQuizNext.classList.add('hidden');
            document.getElementById('btn-restart-quiz').addEventListener('click', loadQuiz);
        }
    }

    // --- Executive Summary Mode ---
    async function loadSummary() {
        try {
            const res = await fetch('/api/summary');
            const data = await res.json();

            elements.summaryOverviewText.textContent = data.overview || 'Upload academic notes to generate an executive study guide.';

            // Render Formulas
            elements.summaryFormulasGrid.innerHTML = '';
            if (data.formulas && data.formulas.length > 0) {
                data.formulas.forEach(f => {
                    const card = document.createElement('div');
                    card.className = 'formula-card';
                    card.innerHTML = `
                        <span class="formula-name">${escapeHtml(f.name)} (p.${f.page})</span>
                        <div class="formula-text">${escapeHtml(f.formula)}</div>
                    `;
                    elements.summaryFormulasGrid.appendChild(card);
                });
            } else {
                elements.summaryFormulasGrid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No mathematical formulas detected in the current notes.</p>';
            }

            // Render Modules
            elements.summaryModulesGrid.innerHTML = '';
            if (data.modules && data.modules.length > 0) {
                data.modules.forEach(m => {
                    const card = document.createElement('div');
                    card.className = 'module-card';
                    card.innerHTML = `
                        <div class="module-title">${escapeHtml(m.title)} <span style="font-size: 0.75rem; color: var(--accent-cyan); font-family: monospace;">(p.${m.page})</span></div>
                        <p class="module-summary">${escapeHtml(m.summary)}</p>
                    `;
                    elements.summaryModulesGrid.appendChild(card);
                });
            } else {
                elements.summaryModulesGrid.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No distinct modules found.</p>';
            }
        } catch (e) {
            console.error('Failed to load summary:', e);
        }
    }

    // --- Chunks Explorer Mode ---
    async function loadChunks(search = '') {
        try {
            const queryParam = search ? `?search=${encodeURIComponent(search)}` : '';
            const res = await fetch(`/api/chunks${queryParam}`);
            const data = await res.json();
            state.allChunks = data.chunks || [];
            elements.chunksCountLabel.textContent = `Showing ${state.allChunks.length} chunks (from ${data.total_matched} total matches)`;

            elements.chunksResultsGrid.innerHTML = '';
            state.allChunks.forEach(chunk => {
                const card = document.createElement('div');
                card.className = 'chunk-card';
                card.innerHTML = `
                    <div class="chunk-header-row">
                        <span class="chunk-id-tag">${escapeHtml(chunk.chunk_id)}</span>
                        <span class="page-tag">${escapeHtml(chunk.doc_name)} | p.${chunk.page}</span>
                    </div>
                    <div style="font-weight: 600; font-size: 0.85rem; color: var(--accent-cyan);">${escapeHtml(chunk.section || 'General')}</div>
                    <p class="chunk-text-preview">${escapeHtml(chunk.text)}</p>
                `;
                card.addEventListener('click', () => {
                    openCitationModal({
                        doc_name: chunk.doc_name,
                        page: chunk.page,
                        relevance: 100,
                        section: chunk.section,
                        snippet: chunk.text
                    });
                });
                elements.chunksResultsGrid.appendChild(card);
            });
        } catch (e) {
            console.error('Failed to load chunks:', e);
        }
    }

    // --- Settings Modal ---
    function openSettingsModal() {
        elements.settingsModal.classList.remove('hidden');
    }

    function closeSettingsModal() {
        elements.settingsModal.classList.add('hidden');
    }

    async function saveSettings() {
        const apiKey = elements.settingsApiKey.value.trim();
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey })
            });
            const data = await res.json();
            showNotification(`Settings updated: Active Engine is now ${data.engine_mode}`);
            closeSettingsModal();
            await refreshStatus();
        } catch (e) {
            alert('Failed to save settings: ' + e.message);
        }
    }

    // --- Event Listeners ---
    function setupEventListeners() {
        // Tab switching
        elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.getAttribute('data-tab');
                switchTab(tab);
            });
        });

        // Quick sample notes & clear all
        elements.btnQuickSample.addEventListener('click', loadSampleNotes);
        elements.btnClearAllDocs.addEventListener('click', clearAllDocuments);

        // Settings modal
        elements.btnOpenSettings.addEventListener('click', openSettingsModal);
        elements.btnCloseSettingsModal.addEventListener('click', closeSettingsModal);
        elements.btnCancelSettings.addEventListener('click', closeSettingsModal);
        elements.btnSaveSettings.addEventListener('click', saveSettings);

        // Citation modal
        elements.btnCloseCiteModal.addEventListener('click', () => elements.citationModal.classList.add('hidden'));
        elements.btnCiteDone.addEventListener('click', () => elements.citationModal.classList.add('hidden'));

        // Dropzone & File browsing
        elements.btnBrowseFiles.addEventListener('click', () => elements.pdfFileInput.click());
        elements.pdfFileInput.addEventListener('change', (e) => uploadFiles(e.target.files));

        elements.pdfDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            elements.pdfDropzone.classList.add('drag-over');
        });

        elements.pdfDropzone.addEventListener('dragleave', () => {
            elements.pdfDropzone.classList.remove('drag-over');
        });

        elements.pdfDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            elements.pdfDropzone.classList.remove('drag-over');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                uploadFiles(e.dataTransfer.files);
            }
        });

        // Chat Submission & Textarea
        elements.chatForm.addEventListener('submit', handleChatSubmit);
        elements.chatUserInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleChatSubmit();
            }
        });
        elements.chatUserInput.addEventListener('input', () => {
            autoResizeTextarea(elements.chatUserInput);
        });

        // Starter Chips
        elements.starterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                elements.chatUserInput.value = query;
                handleChatSubmit();
            });
        });

        // Flashcards Controls
        elements.flashcardElement.addEventListener('click', flipFlashcard);
        elements.btnFcFlip.addEventListener('click', flipFlashcard);
        elements.btnFcPrev.addEventListener('click', prevFlashcard);
        elements.btnFcNext.addEventListener('click', nextFlashcard);
        elements.btnRefreshFlashcards.addEventListener('click', loadFlashcards);

        // Quiz Controls
        elements.btnQuizNext.addEventListener('click', nextQuizQuestion);
        elements.btnRefreshQuiz.addEventListener('click', loadQuiz);

        // Summary Controls
        elements.btnRefreshSummary.addEventListener('click', loadSummary);

        // Chunk Search Filter
        let searchTimeout;
        elements.chunkSearchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadChunks(e.target.value.trim());
            }, 300);
        });

        // Keyboard navigation for flashcards
        document.addEventListener('keydown', (e) => {
            if (state.activeTab === 'flashcards') {
                if (e.code === 'Space') {
                    e.preventDefault();
                    flipFlashcard();
                } else if (e.key === 'ArrowLeft') {
                    prevFlashcard();
                } else if (e.key === 'ArrowRight') {
                    nextFlashcard();
                }
            }
        });
    }

    // --- Utilities ---
    function autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 140) + 'px';
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = escapeHtml(text);

        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold & Italic
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Code blocks
        html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Blockquotes
        html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');

        // Bullet lists
        html = html.replace(/^\s*[-•]\s+(.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        // Line breaks
        html = html.replace(/\n\n/g, '<br/><br/>');

        return html;
    }

    function showNotification(msg) {
        const notif = document.createElement('div');
        notif.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #10B981;
            color: #FFFFFF;
            padding: 0.75rem 1.4rem;
            border-radius: 12px;
            font-size: 0.88rem;
            font-weight: 600;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            animation: fadeIn 0.3s ease;
        `;
        notif.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${escapeHtml(msg)}`;
        document.body.appendChild(notif);
        setTimeout(() => {
            notif.style.opacity = '0';
            notif.style.transition = 'opacity 0.3s ease';
            setTimeout(() => notif.remove(), 300);
        }, 3200);
    }

    // Start App
    init();
});
