/**
 * AI Customer Feedback Analyzer - Core Frontend Application
 * Handles API communication, dynamic Canvas chart rendering, role switches, and real-time NLP testing.
 */

const state = {
    activeRole: "SMB Owner", // "SMB Owner" | "Support Manager" | "System Admin"
    currentTab: "dashboard",
    sources: [],
    metrics: null,
    trends: [],
    themes: [],
    alerts: [],
    urgentItems: [],
    selectedCsvFile: null
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initRoleSelector();
    initFilters();
    initLiveTester();
    initCsvUpload();
    initActions();
    
    // Initial Data Fetch
    loadInitialData();
});

// Navigation Handling
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    state.currentTab = tabId;
    
    // Update nav active state
    document.querySelectorAll(".nav-item").forEach(b => {
        b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
    });

    // Update pane active state
    document.querySelectorAll(".tab-pane").forEach(pane => {
        pane.classList.toggle("active", pane.id === `tab-${tabId}`);
    });

    // Page title update
    const titles = {
        "dashboard": "Executive CX Dashboard",
        "urgent-feed": "Urgent Action Queue",
        "live-tester": "Interactive NLP Pipeline Sandbox",
        "ingest-data": "Data Ingestion & Connected Channels",
        "alerts-tab": "Statistical Anomaly Alerts",
        "admin-tab": "System Administration & RBAC"
    };
    const titleEl = document.getElementById("page-title");
    if (titleEl && titles[tabId]) {
        titleEl.textContent = titles[tabId];
    }

    // Refresh charts if dashboard selected
    if (tabId === "dashboard" && state.trends.length > 0) {
        renderTrendChart(state.trends);
    }
}

// Role-Based Access Control Switcher (Table 2)
function initRoleSelector() {
    const roleSelect = document.getElementById("role-select");
    if (!roleSelect) return;

    roleSelect.addEventListener("change", (e) => {
        state.activeRole = e.target.value;
        applyRolePermissions();
        showToast(`Switched active role to: ${state.activeRole}`);
    });
}

function applyRolePermissions() {
    const isOwner = state.activeRole === "SMB Owner";
    const isManager = state.activeRole === "Support Manager";
    const isAdmin = state.activeRole === "System Admin";

    // Admin-only tabs
    const adminNav = document.querySelector(".admin-only-tab");
    if (adminNav) {
        adminNav.style.display = isAdmin ? "flex" : "none";
    }

    // Export button (Owner & Manager)
    const exportBtn = document.getElementById("btn-export-csv");
    if (exportBtn) {
        exportBtn.style.display = (isOwner || isManager) ? "inline-flex" : "none";
    }

    // If Support Manager, auto highlight Urgent Queue
    if (isManager && state.currentTab === "dashboard") {
        switchTab("urgent-feed");
    }
}

// Data Fetching & Sync
async function loadInitialData() {
    await fetchSources();
    await fetchMetrics();
    await fetchTrends();
    await fetchThemes();
    await fetchAlerts();
    await fetchUrgentQueue();
    await fetchAdminUsers();
}

// Fetch Sources
async function fetchSources() {
    try {
        const res = await fetch("/api/sources");
        if (!res.ok) return;
        state.sources = await res.json();
        
        // Populate dropdowns
        const filterSource = document.getElementById("filter-source");
        const testerSource = document.getElementById("tester-source");
        const uploadSource = document.getElementById("upload-source-id");

        if (filterSource) {
            filterSource.innerHTML = '<option value="">All Channels (Multi-Source View)</option>' + 
                state.sources.map(s => `<option value="${s.source_id}">${s.name} (${s.source_type})</option>`).join("");
        }

        if (testerSource) {
            testerSource.innerHTML = state.sources.map(s => `<option value="${s.source_id}">${s.name}</option>`).join("");
        }

        if (uploadSource) {
            uploadSource.innerHTML = state.sources.map(s => `<option value="${s.source_id}">${s.name}</option>`).join("");
        }

        renderSourcesList();
    } catch (err) {
        console.error("Error loading sources:", err);
    }
}

// Fetch Metrics (NSS, Counts)
async function fetchMetrics(sourceId = "", days = 30) {
    try {
        const url = `/api/analytics/metrics?days=${days}${sourceId ? `&source_id=${sourceId}` : ""}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        state.metrics = data;

        // Update Hero NSS
        const nssEl = document.getElementById("metric-nss");
        const fillBar = document.getElementById("nss-fill-bar");
        if (nssEl) {
            nssEl.textContent = (data.net_sentiment_score > 0 ? "+" : "") + data.net_sentiment_score.toFixed(1);
            if (data.net_sentiment_score > 20) {
                nssEl.style.color = "#34d399";
            } else if (data.net_sentiment_score < -10) {
                nssEl.style.color = "#f87171";
            } else {
                nssEl.style.color = "#fbbf24";
            }
        }

        if (fillBar) {
            // Map -100 to +100 range to 0% to 100%
            const pct = Math.min(100, Math.max(0, (data.net_sentiment_score + 100) / 2));
            fillBar.style.width = `${pct}%`;
        }

        // Total Volume
        document.getElementById("metric-total").textContent = data.total_feedback.toLocaleString();

        // Split Bar
        document.getElementById("split-pos").style.width = `${data.positive_pct}%`;
        document.getElementById("split-neu").style.width = `${data.neutral_pct}%`;
        document.getElementById("split-neg").style.width = `${data.negative_pct}%`;

        document.getElementById("pct-pos").textContent = `${data.positive_pct}%`;
        document.getElementById("pct-neu").textContent = `${data.neutral_pct}%`;
        document.getElementById("pct-neg").textContent = `${data.negative_pct}%`;

        // Urgent & Rating
        document.getElementById("metric-urgent").textContent = data.urgent_complaints_count;
        document.getElementById("metric-rating").textContent = `${data.avg_rating.toFixed(1)}★`;
        document.getElementById("metric-alerts-meta").textContent = `${data.active_alerts_count} active anomalies detected`;

        // Nav Badges
        document.getElementById("nav-urgent-count").textContent = data.urgent_complaints_count;
        document.getElementById("nav-alert-count").textContent = data.active_alerts_count;

    } catch (err) {
        console.error("Error loading metrics:", err);
    }
}

// Fetch Trends & Channels
async function fetchTrends(sourceId = "", days = 14) {
    try {
        const url = `/api/analytics/trends?days=${days}${sourceId ? `&source_id=${sourceId}` : ""}`;
        const res = await fetch(url);
        if (!res.ok) return;
        state.trends = await res.json();
        renderTrendChart(state.trends);

        // Also fetch channel distribution
        const chanRes = await fetch("/api/analytics/channels");
        if (chanRes.ok) {
            const channels = await chanRes.json();
            renderChannels(channels);
        }
    } catch (err) {
        console.error("Error loading trends:", err);
    }
}

// Render Trend Chart using HTML5 Canvas
function renderTrendChart(trendData) {
    const canvas = document.getElementById("trendCanvas");
    if (!canvas || !trendData || trendData.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 25, right: 30, bottom: 40, left: 40 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Find max total volume for scaling
    const maxVal = Math.max(...trendData.map(d => d.total), 5);
    const stepX = chartW / trendData.length;

    // Draw Grid Lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        // Label
        ctx.fillStyle = "#64748b";
        ctx.font = "10px sans-serif";
        ctx.fillText(Math.round(maxVal - (maxVal / 4) * i), 10, y + 3);
    }

    // Draw Stacked Volume Bars (Positive, Neutral, Negative)
    trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX + stepX * 0.2;
        const barW = Math.max(stepX * 0.6, 6);

        const totalH = (d.total / maxVal) * chartH;
        const posH = d.total > 0 ? (d.positive / d.total) * totalH : 0;
        const neuH = d.total > 0 ? (d.neutral / d.total) * totalH : 0;
        const negH = d.total > 0 ? (d.negative / d.total) * totalH : 0;

        let curY = padding.top + chartH;

        // Negative segment (bottom)
        if (negH > 0) {
            ctx.fillStyle = "rgba(239, 68, 68, 0.75)";
            curY -= negH;
            ctx.fillRect(x, curY, barW, negH);
        }

        // Neutral segment (middle)
        if (neuH > 0) {
            ctx.fillStyle = "rgba(129, 140, 248, 0.75)";
            curY -= neuH;
            ctx.fillRect(x, curY, barW, neuH);
        }

        // Positive segment (top)
        if (posH > 0) {
            ctx.fillStyle = "rgba(16, 185, 129, 0.85)";
            curY -= posH;
            ctx.fillRect(x, curY, barW, posH);
        }

        // Date X label
        if (idx % 2 === 0 || idx === trendData.length - 1) {
            ctx.fillStyle = "#94a3b8";
            ctx.font = "10px sans-serif";
            const shortDate = d.date.slice(5); // MM-DD
            ctx.fillText(shortDate, x - 5, height - 12);
        }
    });

    // Draw NSS Line Overlay
    ctx.beginPath();
    ctx.strokeStyle = "#c084fc";
    ctx.lineWidth = 2.5;

    trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX + stepX * 0.5;
        // Map NSS (-100 to +100) to height
        const nssNorm = (d.nss + 100) / 200;
        const y = padding.top + chartH - nssNorm * chartH;

        if (idx === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // NSS Data Points
    trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX + stepX * 0.5;
        const nssNorm = (d.nss + 100) / 200;
        const y = padding.top + chartH - nssNorm * chartH;

        ctx.fillStyle = "#a855f7";
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
    });
}

// Render Channels List
function renderChannels(channels) {
    const list = document.getElementById("channels-list");
    if (!list) return;

    if (!channels || channels.length === 0) {
        list.innerHTML = '<p class="text-muted">No channel data available.</p>';
        return;
    }

    const maxCount = Math.max(...channels.map(c => c.count), 1);

    list.innerHTML = channels.map(c => {
        const pct = Math.round((c.count / maxCount) * 100);
        const sentBadge = c.avg_sentiment >= 0.25 
            ? '<span class="badge badge-pos">Pos</span>' 
            : (c.avg_sentiment <= -0.25 ? '<span class="badge badge-neg">Neg</span>' : '<span class="badge badge-neu">Neu</span>');

        return `
            <div class="channel-row">
                <div class="channel-info">
                    <span><b>${c.name}</b> (${c.source_type})</span>
                    <span>${c.count} items • ${sentBadge}</span>
                </div>
                <div class="channel-bar-bg">
                    <div class="channel-bar-fill" style="width: ${pct}%;"></div>
                </div>
            </div>
        `;
    }).join("");
}

// Fetch & Render Themes
async function fetchThemes() {
    try {
        const res = await fetch("/api/analytics/themes");
        if (!res.ok) return;
        state.themes = await res.json();
        renderThemes(state.themes);
    } catch (err) {
        console.error("Error loading themes:", err);
    }
}

function renderThemes(themes) {
    const grid = document.getElementById("themes-grid");
    if (!grid) return;

    if (!themes || themes.length === 0) {
        grid.innerHTML = '<p class="text-muted">No themes discovered yet.</p>';
        return;
    }

    grid.innerHTML = themes.map(th => {
        const posW = Math.round((th.positive / th.total_count) * 100);
        const neuW = Math.round((th.neutral / th.total_count) * 100);
        const negW = Math.round((th.negative / th.total_count) * 100);

        return `
            <div class="theme-card">
                <div class="theme-header">
                    <span class="theme-title">${th.label}</span>
                    <span class="theme-count">${th.total_count} items</span>
                </div>
                <div class="theme-keywords">
                    🔑 <i>${th.keywords || "general, topics"}</i>
                </div>
                <div class="theme-bar">
                    <div style="width: ${posW}%; background: var(--success);"></div>
                    <div style="width: ${neuW}%; background: var(--neutral-sentiment);"></div>
                    <div style="width: ${negW}%; background: var(--danger);"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; margin-top: 0.4rem; color: var(--text-muted);">
                    <span>${th.positive} Pos</span>
                    <span>${th.neutral} Neu</span>
                    <span>${th.negative} Neg</span>
                </div>
            </div>
        `;
    }).join("");
}

// Fetch & Render Urgent Complaints Queue (Support Manager View)
async function fetchUrgentQueue(status = "new") {
    try {
        let url = `/api/feedback?urgent_only=true&limit=50`;
        if (status) url += `&status=${status}`;

        const res = await fetch(url);
        if (!res.ok) return;
        state.urgentItems = await res.json();
        renderUrgentTable(state.urgentItems);
    } catch (err) {
        console.error("Error loading urgent feed:", err);
    }
}

function renderUrgentTable(items) {
    const tbody = document.getElementById("urgent-table-body");
    if (!tbody) return;

    if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">🎉 No urgent complaints currently pending in this view!</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(item => {
        const urgencyClass = item.urgency_score >= 80 ? "urgency-critical" : (item.urgency_score >= 55 ? "urgency-high" : "urgency-normal");
        const sentScore = item.sentiment_log ? item.sentiment_log.score.toFixed(2) : "0.00";
        const themeLabel = item.theme ? item.theme.label : "General";

        return `
            <tr>
                <td>
                    <span class="urgency-badge ${urgencyClass}">
                        ${item.urgency_score.toFixed(0)}%
                    </span>
                </td>
                <td><span style="font-weight: 600;">${item.source_name || "Source"}</span></td>
                <td class="feedback-text-cell">
                    <div>${escapeHtml(item.cleaned_text)}</div>
                    ${item.rating ? `<span style="font-size: 0.72rem; color: #fbbf24;">${'★'.repeat(item.rating)} (${item.rating}/5)</span>` : ''}
                </td>
                <td><span class="badge badge-accent">${themeLabel}</span></td>
                <td>
                    <span style="font-family: monospace; font-weight: 700; color: ${sentScore < 0 ? '#f87171' : '#34d399'};">
                        ${sentScore}
                    </span>
                </td>
                <td>
                    <span class="badge ${item.status === 'resolved' ? 'badge-pos' : (item.status === 'in_progress' ? 'badge-neu' : 'badge-neg')}">
                        ${item.status.toUpperCase()}
                    </span>
                </td>
                <td>
                    ${item.status !== 'resolved' ? `
                        <button class="btn btn-sm btn-outline" onclick="updateItemStatus(${item.feedback_id}, 'resolved')">
                            ✓ Resolve
                        </button>
                    ` : '<span style="color: #34d399; font-size: 0.8rem;">Resolved</span>'}
                </td>
            </tr>
        `;
    }).join("");
}

// 1-Click Update Feedback Status
window.updateItemStatus = async function(feedbackId, newStatus) {
    try {
        const res = await fetch(`/api/feedback/${feedbackId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast(`Complaint #${feedbackId} marked as ${newStatus}`);
            const statusFilter = document.getElementById("urgent-status-filter").value;
            fetchUrgentQueue(statusFilter);
            fetchMetrics();
        }
    } catch (err) {
        showToast("Error updating complaint status", "danger");
    }
};

// Fetch & Render Alerts
async function fetchAlerts() {
    try {
        const res = await fetch("/api/alerts");
        if (!res.ok) return;
        state.alerts = await res.json();
        renderAlerts(state.alerts);
    } catch (err) {
        console.error("Error loading alerts:", err);
    }
}

function renderAlerts(alerts) {
    const feed = document.getElementById("alerts-feed");
    if (!feed) return;

    if (!alerts || alerts.length === 0) {
        feed.innerHTML = `<p style="padding: 2rem; text-align: center; color: var(--text-muted);">No anomaly alerts triggered. Sentiment baseline is healthy.</p>`;
        return;
    }

    feed.innerHTML = alerts.map(a => {
        const sevClass = a.severity === "critical" ? "severity-critical" : (a.severity === "high" ? "severity-high" : "severity-medium");
        const dateStr = new Date(a.triggered_at).toLocaleString();

        return `
            <div class="alert-row">
                <div class="alert-content">
                    <div class="alert-severity-indicator ${sevClass}"></div>
                    <div>
                        <div class="alert-message">${escapeHtml(a.message)}</div>
                        <div class="alert-timestamp">Triggered: ${dateStr} • Channel: ${a.channel} • Status: <b>${a.status}</b></div>
                    </div>
                </div>
                <div>
                    ${a.status === 'active' ? `
                        <button class="btn btn-sm btn-outline" onclick="acknowledgeAlert(${a.alert_id})">
                            Acknowledge
                        </button>
                    ` : '<span style="color: var(--text-muted); font-size: 0.8rem;">Acknowledged</span>'}
                </div>
            </div>
        `;
    }).join("");
}

window.acknowledgeAlert = async function(alertId) {
    try {
        const res = await fetch(`/api/alerts/${alertId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: "acknowledged" })
        });
        if (res.ok) {
            showToast(`Alert #${alertId} acknowledged.`);
            fetchAlerts();
            fetchMetrics();
        }
    } catch (err) {
        showToast("Error updating alert", "danger");
    }
};

// Render Connected Sources List in Ingestion Tab
function renderSourcesList() {
    const container = document.getElementById("sources-management-list");
    if (!container) return;

    container.innerHTML = state.sources.map(s => {
        const lastSync = s.last_synced_at ? new Date(s.last_synced_at).toLocaleTimeString() : "Never synced";
        return `
            <div class="source-item-card">
                <div class="source-item-info">
                    <h4>${s.name}</h4>
                    <span class="source-item-meta">Type: ${s.source_type} • Status: <b style="color: #34d399;">${s.status}</b> • Last Synced: ${lastSync}</span>
                </div>
                <div>
                    <button class="btn btn-sm btn-primary" onclick="syncSourceDemo(${s.source_id})">
                        ⚡ Sync Demo Reviews
                    </button>
                </div>
            </div>
        `;
    }).join("");
}

window.syncSourceDemo = async function(sourceId) {
    try {
        showToast("Syncing realistic reviews from source API...");
        const res = await fetch(`/api/sources/${sourceId}/sync-demo`, { method: "POST" });
        if (res.ok) {
            const data = await res.json();
            showToast(`Synced ${data.synced_count} new reviews. Alerts: ${data.alerts_triggered}`);
            loadInitialData();
        }
    } catch (err) {
        showToast("Failed to sync source reviews", "danger");
    }
};

// Live NLP Cascade Sandbox (Tab 3)
function initLiveTester() {
    const form = document.getElementById("tester-form");
    const presetBtn = document.getElementById("btn-load-preset");

    const PRESETS = [
        "Charged twice on order #8849! Called support at 9820011223 but the agent was rude and hung up. Total scam, refund my money!",
        "The newly released Android update is brilliant. Battery drain is fixed and the UI feels butter smooth!",
        "Package arrived completely damaged and 8 days late. Tracking number never showed updates.",
        "Average customer care response. Took about two days to reply, but solved the query."
    ];

    if (presetBtn) {
        presetBtn.addEventListener("click", () => {
            const randomSample = PRESETS[Math.floor(Math.random() * PRESETS.length)];
            document.getElementById("tester-text").value = randomSample;
        });
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = document.getElementById("tester-text").value.trim();
            const ratingVal = document.getElementById("tester-rating").value;
            const sourceId = document.getElementById("tester-source").value;

            if (!text) {
                showToast("Please enter feedback text to test.", "warning");
                return;
            }

            const statusBadge = document.getElementById("inference-status");
            statusBadge.textContent = "Inferencing...";

            try {
                const res = await fetch("/api/feedback/single", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        source_id: parseInt(sourceId) || 1,
                        text: text,
                        rating: ratingVal ? parseInt(ratingVal) : null
                    })
                });

                if (res.ok) {
                    const result = await res.json();
                    statusBadge.textContent = "Analysis Complete";

                    // Update UI diagnostic inspection
                    document.getElementById("diag-cleaned").textContent = result.cleaned_text;
                    
                    const sentEl = document.getElementById("diag-sentiment");
                    sentEl.textContent = result.sentiment.toUpperCase();
                    sentEl.style.color = result.sentiment === "positive" ? "#34d399" : (result.sentiment === "negative" ? "#f87171" : "#a5b4fc");

                    document.getElementById("diag-score").textContent = (result.sentiment_score > 0 ? "+" : "") + result.sentiment_score.toFixed(3);
                    
                    const confPct = Math.round(result.confidence * 100);
                    document.getElementById("diag-conf-bar").style.width = `${confPct}%`;
                    document.getElementById("diag-conf-text").textContent = `${confPct}% Confidence`;

                    document.getElementById("diag-theme").textContent = result.theme;

                    document.getElementById("diag-urgency").textContent = result.urgency_score.toFixed(0);
                    const urgencyBadge = document.getElementById("diag-urgency-badge");
                    if (result.urgency_score >= 70) {
                        urgencyBadge.className = "badge badge-neg";
                        urgencyBadge.textContent = "CRITICAL ACTION REQUIRED";
                    } else if (result.urgency_score >= 40) {
                        urgencyBadge.className = "badge badge-neu";
                        urgencyBadge.textContent = "Elevated Risk";
                    } else {
                        urgencyBadge.className = "badge badge-outline";
                        urgencyBadge.textContent = "Normal Priority";
                    }

                    showToast("Feedback scored and added to system!");
                    loadInitialData();
                }
            } catch (err) {
                statusBadge.textContent = "Error";
                showToast("Inference error occurred", "danger");
            }
        });
    }
}

// Bulk CSV Upload Handling (Tab 4)
function initCsvUpload() {
    const dropZone = document.getElementById("csv-drop-zone");
    const fileInput = document.getElementById("csv-file-input");
    const fileInfo = document.getElementById("selected-file-info");
    const submitBtn = document.getElementById("btn-submit-csv");
    const form = document.getElementById("csv-upload-form");
    const uploadResult = document.getElementById("upload-result");

    if (!dropZone || !fileInput) return;

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
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.name.endsWith(".csv")) {
            showToast("Please choose a valid .csv file.", "warning");
            return;
        }
        state.selectedCsvFile = file;
        fileInfo.textContent = `Selected File: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileInfo.classList.remove("hidden");
        submitBtn.disabled = false;
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!state.selectedCsvFile) return;

            const sourceId = document.getElementById("upload-source-id").value;
            const formData = new FormData();
            formData.append("file", state.selectedCsvFile);
            formData.append("source_id", sourceId);

            submitBtn.disabled = true;
            submitBtn.textContent = "Processing and Scoring Records...";

            try {
                const res = await fetch("/api/feedback/upload-csv", {
                    method: "POST",
                    body: formData
                });

                if (res.ok) {
                    const data = await res.json();
                    uploadResult.className = "upload-alert success";
                    uploadResult.classList.remove("hidden");
                    uploadResult.innerHTML = `
                        <b>Ingestion Successful!</b><br/>
                        • Processed & Scored: <b>${data.processed}</b> feedback items<br/>
                        • Duplicates Discarded: <b>${data.duplicates_skipped}</b><br/>
                        • Anomaly Alerts Triggered: <b>${data.alerts_triggered}</b>
                    `;
                    showToast(`Ingested ${data.processed} reviews from ${data.filename}`);
                    loadInitialData();
                } else {
                    throw new Error("Failed upload");
                }
            } catch (err) {
                showToast("CSV ingestion failed. Check formatting.", "danger");
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = "Process & Ingest CSV";
            }
        });
    }
}

// Initialise Button Actions & Filter Listeners
function initActions() {
    const refreshBtn = document.getElementById("btn-refresh");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            showToast("Refreshing metrics & trends...");
            const src = document.getElementById("filter-source").value;
            const days = document.getElementById("filter-time").value;
            fetchMetrics(src, days);
            fetchTrends(src, days);
        });
    }

    // Export CSV
    const exportBtn = document.getElementById("btn-export-csv");
    if (exportBtn) {
        exportBtn.addEventListener("click", () => {
            const src = document.getElementById("filter-source").value;
            window.location.href = `/api/analytics/export-csv${src ? `?source_id=${src}` : ""}`;
            showToast("Generating and downloading full analysis CSV...");
        });
    }

    // Simulate Anomaly Alert
    const simAlertBtn = document.getElementById("btn-simulate-alert");
    if (simAlertBtn) {
        simAlertBtn.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/alerts/simulate", { method: "POST" });
                if (res.ok) {
                    showToast("Simulated anomaly alert generated!");
                    fetchAlerts();
                    fetchMetrics();
                }
            } catch (err) {
                showToast("Simulation trigger failed", "danger");
            }
        });
    }

    // Urgent Status Filter
    const urgentStatusFilter = document.getElementById("urgent-status-filter");
    if (urgentStatusFilter) {
        urgentStatusFilter.addEventListener("change", (e) => {
            fetchUrgentQueue(e.target.value);
        });
    }
}

function initFilters() {
    const filterSource = document.getElementById("filter-source");
    const filterTime = document.getElementById("filter-time");

    if (filterSource) {
        filterSource.addEventListener("change", () => {
            const src = filterSource.value;
            const days = filterTime.value;
            fetchMetrics(src, days);
            fetchTrends(src, days);
        });
    }

    if (filterTime) {
        filterTime.addEventListener("change", () => {
            const src = filterSource.value;
            const days = filterTime.value;
            fetchMetrics(src, days);
            fetchTrends(src, days);
        });
    }
}

// Fetch Admin Users (Tab 6)
async function fetchAdminUsers() {
    try {
        const res = await fetch("/api/auth/users");
        if (!res.ok) return;
        const users = await res.json();
        const tbody = document.getElementById("admin-users-table");
        if (tbody) {
            tbody.innerHTML = users.map(u => `
                <tr>
                    <td><span class="badge badge-accent">${u.role}</span></td>
                    <td><b>${u.name}</b></td>
                    <td>${u.email}</td>
                    <td><span style="color: #34d399;">Active</span></td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error("Error loading users:", err);
    }
}

// Utility: Toast Notifications
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Utility: HTML Escaping
function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
