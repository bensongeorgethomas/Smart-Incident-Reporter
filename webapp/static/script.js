/**
 * Smart Incident Reporter – Civic Intelligence Dashboard
 * Frontend logic: drag-and-drop upload (image + video), status polling,
 * and comprehensive civic intelligence result rendering.
 */

// ── DOM elements ────────────────────────────────────────────────────────────
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const previewContainer = document.getElementById("previewContainer");
const previewImage = document.getElementById("previewImage");
const previewVideo = document.getElementById("previewVideo");
const previewName = document.getElementById("previewName");
const previewSize = document.getElementById("previewSize");
const previewType = document.getElementById("previewType");
const uploadBtn = document.getElementById("uploadBtn");
const cancelBtn = document.getElementById("cancelBtn");
const uploadSection = document.getElementById("uploadSection");
const processingSection = document.getElementById("processingSection");
const processingStatus = document.getElementById("processingStatus");
const processingDetail = document.getElementById("processingDetail");
const progressFill = document.getElementById("progressFill");
const resultsSection = document.getElementById("resultsSection");
const resultThumbnail = document.getElementById("resultThumbnail");
const fileInfo = document.getElementById("fileInfo");
const topLabel = document.getElementById("topLabel");
const labelsList = document.getElementById("labelsList");
const safesearchStatus = document.getElementById("safesearchStatus");
const safesearchDetails = document.getElementById("safesearchDetails");
const newUploadBtn = document.getElementById("newUploadBtn");
const toggleHistory = document.getElementById("toggleHistory");
const historySection = document.getElementById("historySection");
const historyGrid = document.getElementById("historyGrid");
const closeHistory = document.getElementById("closeHistory");

// Civic Intelligence elements
const severityBanner = document.getElementById("severityBanner");
const severityFill = document.getElementById("severityFill");
const severityLevel = document.getElementById("severityLevel");
const severityBannerLabel = document.getElementById("severityBannerLabel");
const urgencyBadge = document.getElementById("urgencyBadge");
const sceneDescription = document.getElementById("sceneDescription");
const incidentTypeBadge = document.getElementById("incidentTypeBadge");
const locationTypeBadge = document.getElementById("locationTypeBadge");
const causeContent = document.getElementById("causeContent");
const risksTimeline = document.getElementById("risksTimeline");
const impactContent = document.getElementById("impactContent");
const actionsList = document.getElementById("actionsList");
const videoCard = document.getElementById("videoCard");
const videoContent = document.getElementById("videoContent");
const envContent = document.getElementById("envContent");
const justificationText = document.getElementById("justificationText");

let selectedFile = null;

// ── Drag & Drop ─────────────────────────────────────────────────────────────
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file && (file.type.startsWith("image/") || file.type.startsWith("video/"))) {
        handleFileSelect(file);
    }
});

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
    }
});

// ── File Selection ──────────────────────────────────────────────────────────
function handleFileSelect(file) {
    selectedFile = file;
    const isVideo = file.type.startsWith("video/");

    previewName.textContent = file.name;
    previewSize.textContent = formatBytes(file.size);
    previewType.textContent = isVideo ? "📹 Video" : "🖼️ Image";

    if (isVideo) {
        previewImage.style.display = "none";
        previewVideo.style.display = "block";
        previewVideo.src = URL.createObjectURL(file);
    } else {
        previewVideo.style.display = "none";
        previewImage.style.display = "block";
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    dropZone.style.display = "none";
    previewContainer.style.display = "block";
}

cancelBtn.addEventListener("click", () => {
    selectedFile = null;
    previewContainer.style.display = "none";
    dropZone.style.display = "block";
    fileInput.value = "";
    previewImage.src = "";
    previewVideo.src = "";
});

// ── Upload ──────────────────────────────────────────────────────────────────
uploadBtn.addEventListener("click", async () => {
    if (!selectedFile) return;

    uploadSection.style.display = "none";
    resultsSection.style.display = "none";
    historySection.style.display = "none";
    processingSection.style.display = "block";
    processingStatus.textContent = "Uploading to Cloud Storage...";
    processingDetail.textContent = "Preparing for AI analysis";
    progressFill.style.width = "10%";

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Upload failed");
        }

        const result = await response.json();
        progressFill.style.width = "30%";
        processingStatus.textContent = "Running Vision AI label detection...";
        processingDetail.textContent = "Then Gemini Civic Intelligence analysis";

        startPolling(result.filename);
    } catch (error) {
        processingSection.style.display = "none";
        uploadSection.style.display = "block";
        previewContainer.style.display = "none";
        dropZone.style.display = "block";
        alert("Upload failed: " + error.message);
    }
});

// ── Polling ─────────────────────────────────────────────────────────────────
function startPolling(filename) {
    let attempts = 0;
    const maxAttempts = 90; // 90 × 3s = 4.5 minutes (Gemini can take time)
    const phases = [
        { at: 0, pct: "35%", status: "Vision AI processing...", detail: "Label detection & SafeSearch" },
        { at: 5, pct: "50%", status: "Gemini analysing scene...", detail: "Contextual understanding in progress" },
        { at: 10, pct: "60%", status: "Assessing severity & risks...", detail: "Predictive risk analysis" },
        { at: 15, pct: "70%", status: "Evaluating public impact...", detail: "Safety impact estimation" },
        { at: 20, pct: "80%", status: "Generating recommendations...", detail: "Compiling final report" },
        { at: 25, pct: "90%", status: "Almost done...", detail: "Finalising civic intelligence report" },
    ];

    const interval = setInterval(async () => {
        attempts++;

        // Update progress phases
        for (const phase of phases) {
            if (attempts === phase.at) {
                progressFill.style.width = phase.pct;
                processingStatus.textContent = phase.status;
                processingDetail.textContent = phase.detail;
            }
        }

        if (attempts >= maxAttempts) {
            clearInterval(interval);
            processingSection.style.display = "none";
            uploadSection.style.display = "block";
            dropZone.style.display = "block";
            previewContainer.style.display = "none";
            alert("Processing timed out. The Cloud Function may still be running — try checking history later.");
            return;
        }

        try {
            const res = await fetch(`/api/status/${filename}`);
            const data = await res.json();

            if (data.processed) {
                clearInterval(interval);
                progressFill.style.width = "100%";
                processingStatus.textContent = "Analysis complete!";
                setTimeout(() => {
                    processingSection.style.display = "none";
                    showResults(data);
                }, 600);
            }
        } catch (err) {
            console.error("Polling error:", err);
        }
    }, 3000);
}

// ── Results Display ─────────────────────────────────────────────────────────
function showResults(data) {
    resultsSection.style.display = "block";

    // Thumbnail
    resultThumbnail.src = data.thumbnail;
    fileInfo.textContent = data.filename;

    // Vision AI Labels
    if (data.top_label && data.top_label !== "N/A") {
        topLabel.textContent = data.top_label;
        topLabel.style.display = "block";
    } else {
        topLabel.style.display = "none";
    }

    labelsList.innerHTML = "";
    if (data.labels && data.labels.length > 0) {
        data.labels.forEach((label) => {
            const tag = document.createElement("span");
            tag.className = "label-tag";
            tag.textContent = label;
            labelsList.appendChild(tag);
        });
    }

    // SafeSearch
    if (data.is_flagged) {
        safesearchStatus.className = "safesearch-status flagged";
        safesearchStatus.textContent = "⚠️ Content Flagged";
    } else {
        safesearchStatus.className = "safesearch-status safe";
        safesearchStatus.textContent = "✅ Content Safe";
    }

    safesearchDetails.innerHTML = "";
    if (data.safe_search) {
        Object.entries(data.safe_search).forEach(([key, value]) => {
            const row = document.createElement("div");
            row.className = "safesearch-row";
            row.innerHTML = `<span class="ss-label">${key}</span><span class="ss-value ss-${value.toLowerCase()}">${value}</span>`;
            safesearchDetails.appendChild(row);
        });
    }

    // ── AI Authenticity Check ───────────────────────────────────────────
    const authenticityBanner = document.getElementById("authenticityBanner");
    const authenticityIcon = document.getElementById("authenticityIcon");
    const authenticityTitle = document.getElementById("authenticityTitle");
    const authenticityDetail = document.getElementById("authenticityDetail");
    const authenticityIndicators = document.getElementById("authenticityIndicators");

    if (data.ai_generated) {
        authenticityBanner.style.display = "flex";
        authenticityBanner.className = "authenticity-banner ai-fake";
        authenticityIcon.textContent = "🤖";
        authenticityTitle.textContent = `AI-Generated Image Detected (${(data.ai_confidence || "medium").toUpperCase()} confidence)`;
        authenticityDetail.textContent = `Recommendation: ${(data.ai_recommendation || "reject").toUpperCase()} — This image appears to be artificially generated and should not be used for incident reporting.`;

        authenticityIndicators.innerHTML = "";
        if (data.ai_indicators && data.ai_indicators.length > 0) {
            const heading = document.createElement("strong");
            heading.textContent = "Detection Indicators:";
            authenticityIndicators.appendChild(heading);
            const ul = document.createElement("ul");
            data.ai_indicators.forEach(ind => {
                const li = document.createElement("li");
                li.textContent = ind;
                ul.appendChild(li);
            });
            authenticityIndicators.appendChild(ul);
        }
    } else if (data.ai_generated === false && data.civic_analysis) {
        // Only show "authentic" badge when we have civic analysis (confirming Gemini ran)
        authenticityBanner.style.display = "flex";
        authenticityBanner.className = "authenticity-banner ai-authentic";
        authenticityIcon.textContent = "✅";
        authenticityTitle.textContent = "Authentic Image Verified";
        authenticityDetail.textContent = "This image passed AI-generation detection checks.";
        authenticityIndicators.innerHTML = "";
    } else {
        authenticityBanner.style.display = "none";
    }

    // ── Civic Intelligence ──────────────────────────────────────────────
    const civic = data.civic_analysis;
    if (!civic) {
        // Hide civic-specific cards if no analysis
        document.querySelectorAll(".scene-card, .cause-card, .risks-card, .impact-card, .actions-card, .env-card, .justification-card, .severity-banner")
            .forEach(el => el.style.display = "none");
        return;
    }

    // Show all civic cards
    document.querySelectorAll(".scene-card, .cause-card, .risks-card, .impact-card, .actions-card, .env-card, .justification-card, .severity-banner")
        .forEach(el => el.style.display = "");

    // Severity Banner
    const severity = civic.severity || {};
    const svLevel = severity.level || 0;
    const svLabel = severity.label || "Unknown";
    const pct = (svLevel / 10) * 100;
    severityFill.style.width = `${pct}%`;
    severityFill.className = `severity-fill severity-${getSeverityClass(svLevel)}`;
    severityLevel.textContent = `${svLevel}/10`;
    severityBannerLabel.textContent = svLabel;

    // Urgency badge
    const urgency = (civic.public_safety_impact || {}).urgency_label || data.urgency || "routine";
    urgencyBadge.textContent = urgency.toUpperCase();
    urgencyBadge.className = `urgency-badge urgency-${urgency}`;

    // Scene description
    sceneDescription.textContent = civic.scene_description || "No description available.";
    const incType = civic.incident_type || "other";
    incidentTypeBadge.textContent = incType.replace(/_/g, " ");
    incidentTypeBadge.className = `incident-type-badge type-${incType}`;

    const envCtx = civic.environmental_context || {};
    const locType = envCtx.location_type || "mixed";
    locationTypeBadge.textContent = locType.replace(/_/g, " ");

    // Root Cause
    const rootCause = civic.root_cause_analysis || {};
    causeContent.innerHTML = `
        <div class="cause-main">
            <strong>Probable Cause:</strong> ${rootCause.probable_cause || "Unknown"}
        </div>
        ${rootCause.contributing_factors && rootCause.contributing_factors.length > 0 ? `
        <div class="cause-factors">
            <strong>Contributing Factors:</strong>
            <ul>${rootCause.contributing_factors.map(f => `<li>${f}</li>`).join("")}</ul>
        </div>` : ""}
        <div class="cause-confidence">
            <span class="confidence-badge conf-${rootCause.confidence || "low"}">${(rootCause.confidence || "low").toUpperCase()} confidence</span>
        </div>
    `;

    // Predictive Risks
    const risks = civic.predictive_risks || [];
    risksTimeline.innerHTML = "";
    if (risks.length === 0) {
        risksTimeline.innerHTML = '<p class="no-data">No significant risks predicted.</p>';
    } else {
        risks.forEach((risk) => {
            const riskEl = document.createElement("div");
            riskEl.className = `risk-item risk-prob-${risk.probability || "low"}`;
            riskEl.innerHTML = `
                <div class="risk-header">
                    <span class="risk-probability prob-${risk.probability || "low"}">${(risk.probability || "low").toUpperCase()}</span>
                    <span class="risk-timeframe">${formatTimeframe(risk.timeframe)}</span>
                </div>
                <p class="risk-desc">${risk.risk || ""}</p>
                <p class="risk-mitigation">💡 ${risk.mitigation || "No mitigation suggested."}</p>
            `;
            risksTimeline.appendChild(riskEl);
        });
    }

    // Public Safety Impact
    const impact = civic.public_safety_impact || {};
    impactContent.innerHTML = `
        <div class="impact-stat">
            <div class="impact-icon">👥</div>
            <div>
                <div class="impact-label">Affected Population</div>
                <div class="impact-value">${impact.affected_population_estimate || "Unknown"}</div>
            </div>
        </div>
        ${impact.affected_services && impact.affected_services.length > 0 ? `
        <div class="impact-services">
            <div class="impact-label">Affected Services</div>
            <div class="service-tags">${impact.affected_services.map(s => `<span class="service-tag">${s}</span>`).join("")}</div>
        </div>` : ""}
        ${impact.accessibility_impact ? `
        <div class="impact-accessibility">
            <div class="impact-icon">♿</div>
            <div>
                <div class="impact-label">Accessibility Impact</div>
                <div class="impact-value">${impact.accessibility_impact}</div>
            </div>
        </div>` : ""}
    `;

    // Recommended Actions
    const actions = civic.recommended_actions || [];
    actionsList.innerHTML = "";
    if (actions.length === 0) {
        actionsList.innerHTML = '<p class="no-data">No specific actions recommended.</p>';
    } else {
        actions.sort((a, b) => (a.priority || 5) - (b.priority || 5));
        actions.forEach((action) => {
            const actEl = document.createElement("div");
            actEl.className = "action-item";
            actEl.innerHTML = `
                <span class="action-priority priority-${action.priority || 5}">P${action.priority || "?"}</span>
                <div class="action-details">
                    <p class="action-text">${action.action || ""}</p>
                    <span class="action-party">${action.responsible_party || ""}</span>
                </div>
            `;
            actionsList.appendChild(actEl);
        });
    }

    // Video Analysis (conditional)
    const videoAnalysis = civic.video_analysis;
    if (videoAnalysis) {
        videoCard.style.display = "";
        videoContent.innerHTML = `
            <div class="video-stat">
                <span class="video-label">Trend:</span>
                <span class="video-trend trend-${videoAnalysis.temporal_trend || "stable"}">${(videoAnalysis.temporal_trend || "stable").toUpperCase()}</span>
            </div>
            <div class="video-stat">
                <span class="video-label">Rate of Change:</span>
                <span>${videoAnalysis.rate_of_change || "N/A"}</span>
            </div>
            <div class="video-stat">
                <span class="video-label">Duration Estimate:</span>
                <span>${videoAnalysis.duration_estimate || "N/A"}</span>
            </div>
            ${videoAnalysis.key_moments && videoAnalysis.key_moments.length > 0 ? `
            <div class="video-moments">
                <span class="video-label">Key Moments:</span>
                <ul>${videoAnalysis.key_moments.map(m => `<li>${m}</li>`).join("")}</ul>
            </div>` : ""}
        `;
    } else {
        videoCard.style.display = "none";
    }

    // Environmental Context
    envContent.innerHTML = `
        ${envCtx.time_sensitivity ? `<p><strong>⏰ Time Sensitivity:</strong> ${envCtx.time_sensitivity}</p>` : ""}
        ${envCtx.weather_sensitivity ? `<p><strong>🌧️ Weather Sensitivity:</strong> ${envCtx.weather_sensitivity}</p>` : ""}
    `;

    // Severity Justification
    justificationText.textContent = severity.justification || "No justification provided.";
}

// ── New Upload ──────────────────────────────────────────────────────────────
newUploadBtn.addEventListener("click", () => {
    resultsSection.style.display = "none";
    uploadSection.style.display = "block";
    previewContainer.style.display = "none";
    dropZone.style.display = "block";
    selectedFile = null;
    fileInput.value = "";
});

// ── History ─────────────────────────────────────────────────────────────────
toggleHistory.addEventListener("click", async () => {
    const isVisible = historySection.style.display === "block";

    if (isVisible) {
        historySection.style.display = "none";
        return;
    }

    uploadSection.style.display = "none";
    resultsSection.style.display = "none";
    processingSection.style.display = "none";
    historySection.style.display = "block";
    historyGrid.innerHTML = '<div class="history-empty">Loading history...</div>';

    try {
        const res = await fetch("/api/history");
        const data = await res.json();

        historyGrid.innerHTML = "";

        if (!data.images || data.images.length === 0) {
            historyGrid.innerHTML = '<div class="history-empty">No images processed yet. Upload one above!</div>';
            return;
        }

        data.images.forEach((img) => {
            const item = document.createElement("div");
            item.className = "history-item";
            const svLevel = img.severity_level || 0;
            const svClass = getSeverityClass(svLevel);
            const civicSummary = img.civic_summary;

            item.innerHTML = `
                <img src="${img.thumbnail}" alt="${img.name}" loading="lazy">
                <div class="history-info">
                    <span class="history-name">${img.name}</span>
                    <span class="history-label">${img.top_label}</span>
                    ${svLevel > 0 ? `
                    <div class="history-severity">
                        <span class="severity-dot severity-${svClass}"></span>
                        <span>${img.severity_label || "Unknown"} (${svLevel}/10)</span>
                    </div>` : ""}
                    ${civicSummary ? `<p class="history-scene">${(civicSummary.scene_description || "").substring(0, 100)}${(civicSummary.scene_description || "").length > 100 ? "..." : ""}</p>` : ""}
                    <span class="history-flag ${img.is_flagged ? "flagged" : "safe"}">
                        ${img.is_flagged ? "Flagged" : "Safe"}
                    </span>
                </div>
            `;
            historyGrid.appendChild(item);
        });
    } catch (error) {
        historyGrid.innerHTML = `<div class="history-empty">Failed to load history: ${error.message}</div>`;
    }
});

closeHistory.addEventListener("click", () => {
    historySection.style.display = "none";
    uploadSection.style.display = "block";
    previewContainer.style.display = "none";
    dropZone.style.display = "block";
});

// ── Utility Functions ───────────────────────────────────────────────────────
function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function getSeverityClass(level) {
    if (level <= 2) return "minor";
    if (level <= 4) return "moderate";
    if (level <= 6) return "significant";
    if (level <= 8) return "severe";
    return "critical";
}

function formatTimeframe(tf) {
    const map = {
        within_hours: "⏱️ Within Hours",
        within_days: "📅 Within Days",
        within_weeks: "📆 Within Weeks",
        within_months: "🗓️ Within Months",
    };
    return map[tf] || tf || "Unknown";
}
