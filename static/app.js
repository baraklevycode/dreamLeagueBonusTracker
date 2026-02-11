/* Dream League Bonus Tracker - Frontend */

const API_BASE = "";

const BONUS_ICONS = {
    1: "\u{1F451}",  // crown - Triple Captain
    2: "\u{1F504}",  // arrows - 15 Subs
    3: "\u{1F396}",  // medal - Double Captains
    4: "\u{1F4AA}",  // muscle - Full Squad Points
};

const ALL_BONUSES = [
    { id: 1, name: "Triple Captain" },
    { id: 2, name: "15 Subs" },
    { id: 3, name: "Double Captains" },
    { id: 4, name: "Full Squad Points" },
];

/* === Initialization === */
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });
    document.getElementById("team-form").addEventListener("submit", handleTeamSearch);
    document.getElementById("league-form").addEventListener("submit", handleLeagueSearch);

    // Check auth status on load
    checkAuthStatus();
});

/* === Auth === */
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth/status`);
        const data = await response.json();
        updateAuthUI(data.authenticated, data.email);
    } catch {
        updateAuthUI(false, "");
    }
}

function updateAuthUI(authenticated, email) {
    const dot = document.querySelector(".auth-dot");
    const text = document.getElementById("auth-text");
    const btn = document.getElementById("auth-toggle-btn");

    if (authenticated && email) {
        dot.classList.add("connected");
        text.textContent = `Logged in as ${email}`;
        btn.textContent = "Switch Account";
        btn.onclick = toggleLoginForm;
    } else {
        dot.classList.remove("connected");
        text.textContent = "Not authenticated";
        btn.textContent = "Login";
        btn.onclick = toggleLoginForm;
    }
}

function toggleLoginForm() {
    const overlay = document.getElementById("login-overlay");
    overlay.classList.toggle("visible");
    // Clear form and errors when opening
    if (overlay.classList.contains("visible")) {
        document.getElementById("login-form").reset();
        document.getElementById("login-error").classList.remove("visible");
        document.getElementById("login-email").focus();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const errorEl = document.getElementById("login-error");
    const submitBtn = document.getElementById("login-submit-btn");

    errorEl.classList.remove("visible");
    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || `Login failed (HTTP ${response.status})`);
        }

        const data = await response.json();
        updateAuthUI(data.authenticated, data.email);
        toggleLoginForm();
    } catch (err) {
        errorEl.textContent = err.message;
        errorEl.classList.add("visible");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Login";
    }
}

/* === Tab Switching === */
function switchTab(tabName) {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabName);
    });
    document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.toggle("active", content.id === `tab-${tabName}`);
    });
}

/* === Team Search === */
async function handleTeamSearch(e) {
    e.preventDefault();
    const userId = document.getElementById("user-id-input").value.trim();
    if (!userId) return;

    const resultsEl = document.getElementById("team-results");
    const loaderEl = document.getElementById("team-loader");
    const errorEl = document.getElementById("team-error");

    resultsEl.style.display = "none";
    errorEl.classList.remove("visible");
    loaderEl.classList.add("visible");

    try {
        const response = await fetch(`${API_BASE}/team/${userId}/bonuses`);
        if (!response.ok) {
            const errData = await response.json().catch(() => null);
            const detail = errData && typeof errData === "object" ? (errData.detail || JSON.stringify(errData)) : `HTTP ${response.status}`;
            throw new Error(detail);
        }
        const data = await response.json();
        renderTeamResult(data);
        resultsEl.style.display = "block";
    } catch (err) {
        errorEl.textContent = `Error: ${err.message || String(err)}`;
        errorEl.classList.add("visible");
    } finally {
        loaderEl.classList.remove("visible");
    }
}

function renderTeamResult(team) {
    const container = document.getElementById("team-results");
    container.innerHTML = renderTeamCard(team, true);
}

/* === League Search === */
async function handleLeagueSearch(e) {
    e.preventDefault();
    const leagueId = document.getElementById("league-id-input").value.trim();
    const endpoint = leagueId ? `/league/${leagueId}/bonuses` : "/league/main/bonuses";

    const resultsEl = document.getElementById("league-results");
    const loaderEl = document.getElementById("league-loader");
    const errorEl = document.getElementById("league-error");

    resultsEl.style.display = "none";
    errorEl.classList.remove("visible");
    loaderEl.classList.add("visible");

    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            const errData = await response.json().catch(() => null);
            const detail = errData && typeof errData === "object" ? (errData.detail || JSON.stringify(errData)) : `HTTP ${response.status}`;
            throw new Error(detail);
        }
        const data = await response.json();
        renderLeagueResult(data);
        resultsEl.style.display = "block";
    } catch (err) {
        errorEl.textContent = `Error: ${err.message || String(err)}`;
        errorEl.classList.add("visible");
    } finally {
        loaderEl.classList.remove("visible");
    }
}

function renderLeagueResult(report) {
    const container = document.getElementById("league-results");

    const headerHtml = `
        <div class="league-header">
            <div>
                <h2>${escapeHtml(report.league_name)}</h2>
                <span class="league-meta">Season ${report.season_id} &middot; ${report.teams.length} teams</span>
            </div>
            <div class="points-badge">${report.teams.length} teams loaded</div>
        </div>
    `;

    const teamsHtml = report.teams
        .sort((a, b) => b.total_points - a.total_points)
        .map(team => renderTeamCard(team, false))
        .join("");

    container.innerHTML = headerHtml + teamsHtml;
}

/* === Shared Rendering === */
function renderTeamCard(team, expanded) {
    const usedIds = new Set(team.used_bonuses.map(b => b.bonus_id));

    const bonusGridHtml = ALL_BONUSES.map(bonus => {
        const isUsed = usedIds.has(bonus.id);
        const usedData = team.used_bonuses.find(b => b.bonus_id === bonus.id);
        const statusClass = isUsed ? "used" : "available";
        const statusText = isUsed ? "Used" : "Available";
        const roundInfo = isUsed ? `<div class="bonus-round">Round ${usedData.usage_round_id}</div>` : "";
        const icon = BONUS_ICONS[bonus.id] || "\u{2B50}";

        return `
            <div class="bonus-item ${statusClass}">
                <div class="bonus-icon">${icon}</div>
                <div class="bonus-name">${escapeHtml(bonus.name)}</div>
                <div class="bonus-status">${statusText}</div>
                ${roundInfo}
            </div>
        `;
    }).join("");

    return `
        <div class="team-card">
            <div class="team-card-header" onclick="toggleCard(this)">
                <div class="team-info">
                    <h3>${escapeHtml(team.team_name)}</h3>
                    <span class="team-meta">${escapeHtml(team.creator_name)}</span>
                </div>
                <div class="team-stats">
                    <span class="points-badge">${team.total_points} pts</span>
                    <span class="stat-badge used">${team.used_count} used</span>
                    <span class="stat-badge remaining">${team.remaining_count} left</span>
                </div>
            </div>
            <div class="team-card-body" style="display: ${expanded ? "block" : "none"};">
                <div class="bonus-grid">
                    ${bonusGridHtml}
                </div>
            </div>
        </div>
    `;
}

function toggleCard(headerEl) {
    const body = headerEl.nextElementSibling;
    body.style.display = body.style.display === "none" ? "block" : "none";
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
