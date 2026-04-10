/* ═══════════════════════════════════════════════════════════
   AI Resume Agent — Frontend Logic (No API Key Required)
   ═══════════════════════════════════════════════════════════ */

(() => {
    "use strict";

    const $ = (sel) => document.querySelector(sel);

    // ── DOM Elements ──
    const tabRecruiter = $("#tabRecruiter");
    const tabCandidate = $("#tabCandidate");
    const tabIndicator = $("#tabIndicator");
    const recruiterPanel = $("#recruiterPanel");
    const candidatePanel = $("#candidatePanel");

    const recruiterDropZone = $("#recruiterDropZone");
    const recruiterFileInput = $("#recruiterFile");
    const recruiterFilePreview = $("#recruiterFilePreview");
    const recruiterFileName = $("#recruiterFileName");
    const recruiterFileRemove = $("#recruiterFileRemove");

    const candidateDropZone = $("#candidateDropZone");
    const candidateFileInput = $("#candidateFile");
    const candidateFilePreview = $("#candidateFilePreview");
    const candidateFileName = $("#candidateFileName");
    const candidateFileRemove = $("#candidateFileRemove");

    const jobDescription = $("#jobDescription");
    const analyzeBtn = $("#analyzeBtn");
    const recommendBtn = $("#recommendBtn");

    const recruiterResults = $("#recruiterResults");
    const candidateResults = $("#candidateResults");

    const usageText = $("#usageText");
    const usageBadge = $("#usageBadge");

    let currentRecruiterFile = null;
    let currentCandidateFile = null;

    // ── Background Particles ──
    function createParticles() {
        const container = $("#bgParticles");
        for (let i = 0; i < 6; i++) {
            const p = document.createElement("div");
            p.className = "particle";
            const size = Math.random() * 300 + 100;
            p.style.width = `${size}px`;
            p.style.height = `${size}px`;
            p.style.left = `${Math.random() * 100}%`;
            p.style.top = `${Math.random() * 100}%`;
            p.style.animationDelay = `${Math.random() * 10}s`;
            p.style.animationDuration = `${15 + Math.random() * 15}s`;
            container.appendChild(p);
        }
    }
    createParticles();

    // ── Usage Tracking ──
    async function fetchUsage() {
        try {
            const res = await fetch("/api/usage");
            if (res.ok) {
                const data = await res.json();
                updateUsageDisplay(data.remaining, data.limit);
            }
        } catch (e) {
            // Silently fail — usage display is optional
        }
    }

    function updateUsageDisplay(remaining, limit) {
        const used = limit - remaining;
        usageText.textContent = `${remaining}/${limit} left today`;
        if (remaining <= 1) {
            usageBadge.classList.add("usage-low");
        } else {
            usageBadge.classList.remove("usage-low");
        }
    }

    fetchUsage();

    // ── Tab Switching ──
    function switchTab(tab) {
        if (tab === "recruiter") {
            tabRecruiter.classList.add("active");
            tabCandidate.classList.remove("active");
            recruiterPanel.classList.add("active");
            candidatePanel.classList.remove("active");
            tabIndicator.classList.remove("right");
        } else {
            tabCandidate.classList.add("active");
            tabRecruiter.classList.remove("active");
            candidatePanel.classList.add("active");
            recruiterPanel.classList.remove("active");
            tabIndicator.classList.add("right");
        }
    }

    tabRecruiter.addEventListener("click", () => switchTab("recruiter"));
    tabCandidate.addEventListener("click", () => switchTab("candidate"));

    // ── File Upload Helpers ──
    function setupDropZone(dropZone, fileInput, preview, nameEl, removeBtn, setFile) {
        dropZone.addEventListener("click", () => {
            if (!preview.classList.contains("hidden")) return;
            fileInput.click();
        });

        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });

        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });

        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            const file = e.dataTransfer.files[0];
            if (file && file.type === "application/pdf") {
                handleFile(file, preview, nameEl, dropZone, setFile);
            }
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files[0]) {
                handleFile(fileInput.files[0], preview, nameEl, dropZone, setFile);
            }
        });

        removeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            clearFile(preview, nameEl, dropZone, fileInput, setFile);
        });
    }

    function handleFile(file, preview, nameEl, dropZone, setFile) {
        setFile(file);
        nameEl.textContent = file.name;
        preview.classList.remove("hidden");
        dropZone.querySelector(".drop-zone-content").classList.add("hidden");
    }

    function clearFile(preview, nameEl, dropZone, fileInput, setFile) {
        setFile(null);
        nameEl.textContent = "";
        preview.classList.add("hidden");
        dropZone.querySelector(".drop-zone-content").classList.remove("hidden");
        fileInput.value = "";
    }

    setupDropZone(
        recruiterDropZone, recruiterFileInput, recruiterFilePreview,
        recruiterFileName, recruiterFileRemove,
        (f) => { currentRecruiterFile = f; }
    );

    setupDropZone(
        candidateDropZone, candidateFileInput, candidateFilePreview,
        candidateFileName, candidateFileRemove,
        (f) => { currentCandidateFile = f; }
    );

    // ── Button State Helpers ──
    function setLoading(btn, loading) {
        const text = btn.querySelector(".btn-text");
        const loader = btn.querySelector(".btn-loading");
        if (loading) {
            text.classList.add("hidden");
            loader.classList.remove("hidden");
            btn.disabled = true;
        } else {
            text.classList.remove("hidden");
            loader.classList.add("hidden");
            btn.disabled = false;
        }
    }

    // ── Score Circle Renderer ──
    function renderScoreCircle(score) {
        const circumference = 2 * Math.PI * 62;
        const offset = circumference - (score / 100) * circumference;

        let color, badge, badgeClass;
        if (score >= 80) {
            color = "#10b981"; badge = "🟢 Excellent Fit"; badgeClass = "score-high";
        } else if (score >= 50) {
            color = "#f59e0b"; badge = "🟡 Moderate Fit"; badgeClass = "score-mid";
        } else {
            color = "#ef4444"; badge = "🔴 Low Fit"; badgeClass = "score-low";
        }

        return `
            <div class="score-display">
                <div class="score-circle">
                    <svg viewBox="0 0 140 140">
                        <circle class="bg-ring" cx="70" cy="70" r="62"/>
                        <circle class="score-ring" cx="70" cy="70" r="62"
                            stroke="${color}"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${offset}"/>
                    </svg>
                    <div class="score-value">
                        <div class="score-number" style="color:${color}">${score}</div>
                        <div class="score-label">Match Score</div>
                    </div>
                </div>
                <span class="score-badge ${badgeClass}">${badge}</span>
            </div>
        `;
    }

    // ── Handle API response usage data ──
    function handleUsage(data) {
        if (data._usage) {
            updateUsageDisplay(data._usage.remaining, data._usage.limit);
        }
    }

    // ── Recruiter Mode: Analyze ──
    analyzeBtn.addEventListener("click", async () => {
        if (!currentRecruiterFile) {
            showError(recruiterResults, "Please upload a resume PDF first.");
            return;
        }
        if (!jobDescription.value.trim()) {
            showError(recruiterResults, "Please paste a job description.");
            return;
        }

        setLoading(analyzeBtn, true);
        recruiterResults.classList.add("hidden");

        const formData = new FormData();
        formData.append("file", currentRecruiterFile);
        formData.append("job_description", jobDescription.value.trim());

        try {
            const res = await fetch("/api/analyze", { method: "POST", body: formData });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `Server error ${res.status}`);
            }
            const data = await res.json();
            handleUsage(data);
            renderRecruiterResults(data);
        } catch (e) {
            showError(recruiterResults, e.message);
        } finally {
            setLoading(analyzeBtn, false);
        }
    });

    function renderRecruiterResults(data) {
        const score = data.match_score || 0;
        const strong = (data.strong_points || []).map(p => `<li>${esc(p)}</li>`).join("");
        const missing = (data.missing_skills || []).map(s => `<li>${esc(s)}</li>`).join("");
        const suggestions = (data.suggestions || []).map(s => `<div class="suggestion-item">💡 ${esc(s)}</div>`).join("");

        recruiterResults.innerHTML = `
            ${renderScoreCircle(score)}
            <div class="results-grid">
                <div class="glass-card result-card strengths">
                    <h3>✅ Strong Points</h3>
                    <ul>${strong || "<li>No strong points identified.</li>"}</ul>
                </div>
                <div class="glass-card result-card missing">
                    <h3>❌ Missing Skills</h3>
                    <ul>${missing || "<li>No missing skills identified.</li>"}</ul>
                </div>
            </div>
            <div class="suggestions-section">
                <h3>💡 Suggestions to Improve</h3>
                ${suggestions || "<div class='suggestion-item'>No suggestions available.</div>"}
            </div>
        `;
        recruiterResults.classList.remove("hidden");
        recruiterResults.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // ── Candidate Mode: Recommend ──
    recommendBtn.addEventListener("click", async () => {
        if (!currentCandidateFile) {
            showError(candidateResults, "Please upload your resume PDF first.");
            return;
        }

        setLoading(recommendBtn, true);
        candidateResults.classList.add("hidden");

        const formData = new FormData();
        formData.append("file", currentCandidateFile);

        try {
            const res = await fetch("/api/recommend", { method: "POST", body: formData });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || `Server error ${res.status}`);
            }
            const data = await res.json();
            handleUsage(data);
            renderCandidateResults(data);
        } catch (e) {
            showError(candidateResults, e.message);
        } finally {
            setLoading(recommendBtn, false);
        }
    });

    function renderCandidateResults(data) {
        const roles = (data.recommended_roles || []).map(role => {
            const conf = role.confidence || 0;
            let level = "low";
            if (conf >= 75) level = "high";
            else if (conf >= 50) level = "mid";

            return `
                <div class="glass-card role-card">
                    <div class="role-confidence ${level}">${conf}%</div>
                    <div class="role-info">
                        <div class="role-title">${esc(role.title || "Unknown Role")}</div>
                        <div class="role-reason">${esc(role.reason || "")}</div>
                    </div>
                </div>
            `;
        }).join("");

        const industries = (data.industry_fit || []).map(i => `<span class="tag">${esc(i)}</span>`).join("");
        const strengths = (data.current_strengths || []).map(s => `<li>${esc(s)}</li>`).join("");
        const gaps = (data.skill_gaps || []).map(s => `<li>${esc(s)}</li>`).join("");
        const advice = data.career_advice || "No advice available.";

        candidateResults.innerHTML = `
            <h3 style="font-size:1.15rem;font-weight:700;margin-bottom:1rem;">🎯 Recommended Job Roles</h3>
            <div class="roles-list">${roles}</div>

            <div class="results-grid">
                <div class="glass-card result-card">
                    <h3>🏭 Best Industries</h3>
                    <div class="tag-group">${industries || "<span class='tag'>N/A</span>"}</div>
                </div>
                <div class="glass-card result-card strengths">
                    <h3>💪 Your Strengths</h3>
                    <ul>${strengths || "<li>No strengths identified.</li>"}</ul>
                </div>
            </div>

            <div class="glass-card result-card gaps" style="margin-top:1.25rem;">
                <h3>📚 Skills to Learn Next</h3>
                <ul>${gaps || "<li>No skill gaps identified.</li>"}</ul>
            </div>

            <div class="glass-card advice-card">
                <h3>🧭 Career Advice</h3>
                <p>${esc(advice)}</p>
            </div>
        `;
        candidateResults.classList.remove("hidden");
        candidateResults.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // ── Helpers ──
    function showError(container, msg) {
        container.innerHTML = `<div class="error-message">⚠️ ${esc(msg)}</div>`;
        container.classList.remove("hidden");
    }

    function esc(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
})();
