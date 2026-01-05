// Fakeouts Page Logic
let allFakeouts = [];
let filteredFakeouts = [];
let currentFakeoutPage = 1;
let fakeoutsPerPage = 12;
let selectedFakeout = null;

/* =========================
   PAGE LOAD
========================= */
function loadFakeoutsPage(container) {
    container.innerHTML = `
        <h1 class="page-title">Fakeouts Detector</h1>

        <div class="stats-grid">
            <div class="stat-card"><span>Today</span><div id="statToday">-</div></div>
            <div class="stat-card"><span>This Week</span><div id="statWeek">-</div></div>
            <div class="stat-card"><span>This Month</span><div id="statMonth">-</div></div>
        </div>

        <div class="controls">
            <select id="fakeoutSymbolFilter"></select>
            <select id="fakeoutTimeframeFilter"></select>
            <select id="fakeoutTypeFilter"></select>
            <button id="loadFakeoutsBtn">Load Fakeouts</button>
            <button id="clearFakeoutFiltersBtn">Clear Filters</button>
        </div>

        <div id="fakeoutInfo" style="display:none"></div>
        <div id="fakeoutError" class="error" style="display:none"></div>
        <div id="fakeoutContent"></div>

        <div id="fakeoutPagination" style="display:none">
            <button id="fakeoutPrevBtn">← Prev</button>
            <span id="fakeoutPageInfo"></span>
            <button id="fakeoutNextBtn">Next →</button>
        </div>
    `;

    document.getElementById('loadFakeoutsBtn').onclick = loadFakeouts;
    document.getElementById('clearFakeoutFiltersBtn').onclick = clearFakeoutFilters;
    document.getElementById('fakeoutPrevBtn').onclick = prevFakeoutPage;
    document.getElementById('fakeoutNextBtn').onclick = nextFakeoutPage;

    loadFakeoutStats();
}

/* =========================
   DATA LOAD
========================= */
async function loadFakeoutStats() {
    try {
        const r = await fetch(`${API}/fakeouts/stats`);
        const s = await r.json();
        statToday.textContent = s.today ?? 0;
        statWeek.textContent = s.week ?? 0;
        statMonth.textContent = s.month ?? 0;
    } catch {}
}

async function loadFakeouts() {
    try {
        const r = await fetch(`${API}/fakeouts?limit=200`);
        const d = await r.json();
        allFakeouts = d.fakeouts || [];
        applyFakeoutFilters();
    } catch (e) {
        fakeoutError.textContent = e.message;
        fakeoutError.style.display = 'block';
    }
}

/* =========================
   FILTER + PAGINATION
========================= */
function applyFakeoutFilters() {
    filteredFakeouts = [...allFakeouts].sort(
        (a,b)=>new Date(b.timestamp)-new Date(a.timestamp)
    );
    currentFakeoutPage = 1;
    displayFakeoutPage();
}

function displayFakeoutPage() {
    const start = (currentFakeoutPage - 1) * fakeoutsPerPage;
    const page = filteredFakeouts.slice(start, start + fakeoutsPerPage);

    document.getElementById('fakeoutPagination').style.display =
        filteredFakeouts.length > fakeoutsPerPage ? 'block' : 'none';

    document.getElementById('fakeoutPageInfo').textContent =
        `Page ${currentFakeoutPage}`;

    renderFakeoutCards(page);
}

function nextFakeoutPage() {
    if (currentFakeoutPage * fakeoutsPerPage < filteredFakeouts.length) {
        currentFakeoutPage++;
        displayFakeoutPage();
    }
}

function prevFakeoutPage() {
    if (currentFakeoutPage > 1) {
        currentFakeoutPage--;
        displayFakeoutPage();
    }
}

function clearFakeoutFilters() {
    applyFakeoutFilters();
}

/* =========================
   CARDS
========================= */
function renderFakeoutCards(list) {
    fakeoutContent.innerHTML = `
        <div class="fakeouts-grid">
            ${list.map(f=>`
                <div class="fakeout-card" onclick='showFakeoutDetail(${JSON.stringify(f)})'>
                    <strong>${f.symbol.toUpperCase()}</strong>
                    <div>${formatDateTime(f.timestamp)}</div>
                </div>
            `).join('')}
        </div>
    `;
}

/* =========================
   DETAIL VIEW
========================= */
async function showFakeoutDetail(f) {
    app.innerHTML = `
        <button onclick="loadFakeoutsPage(app)">← Back</button>
        <h2>${f.symbol.toUpperCase()} ${f.timeframe}</h2>
        <canvas id="contextCanvas"></canvas>
    `;
    loadContextChart(f);
}

async function loadContextChart(f) {
    const r = await fetch(`${API}/fakeouts/${f.id}?symbol=${f.symbol}&timeframe=${f.timeframe}`);
    const d = await r.json();
    renderContextChart(f, d.context_candles || []);
}

/* =========================
   CHART (FIXED)
========================= */
function renderContextChart(fakeout, candles) {
    const ctx = contextCanvas.getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: candles.map(c => formatTime(c.timestamp)),
            datasets: [{
                label: 'Close',
                data: candles.map(c => +c.close),
                borderWidth: 2
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: ctx =>
                            `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                y: {
                    ticks: {
                        callback: v => v.toFixed(2)
                    }
                }
            }
        }
    });
}

/* =========================
   UTILS
========================= */
function formatDateTime(ts) {
    return new Date(ts).toLocaleString();
}
function formatTime(ts) {
    return new Date(ts).toLocaleTimeString();
}
function formatPrice(v) {
    return v == null ? 'N/A' : `$${(+v).toFixed(2)}`;
}
