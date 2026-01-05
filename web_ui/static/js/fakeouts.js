// Fakeouts Page Logic
let allFakeouts = [];
let filteredFakeouts = [];
let currentFakeoutPage = 1;
let fakeoutsPerPage = 12;
let selectedFakeout = null;

function loadFakeoutsPage(container) {
    container.innerHTML = `
        <h1 class="page-title">Fakeouts Detector</h1>

        <div class="stats-grid" id="fakeoutStats">
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">Today</span>
                    <span class="stat-icon">📊</span>
                </div>
                <div class="stat-value" id="statToday">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">This Week</span>
                    <span class="stat-icon">📈</span>
                </div>
                <div class="stat-value" id="statWeek">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-header">
                    <span class="stat-label">This Month</span>
                    <span class="stat-icon">💾</span>
                </div>
                <div class="stat-value" id="statMonth">-</div>
            </div>
        </div>

        <div class="controls">
            <div class="control-group">
                <label>Symbol</label>
                <select id="fakeoutSymbolFilter">
                    <option value="">All Symbols</option>
                    <option value="btcusdt">BTCUSDT</option>
                    <option value="ethusdt">ETHUSDT</option>
                    <option value="ltcusdt">LTCUSDT</option>
                    <option value="xrpusdt">XRPUSDT</option>
                    <option value="dogeusdt">DOGEUSDT</option>
                    <option value="linkusdt">LINKUSDT</option>
                    <option value="adausdt">ADAUSDT</option>
                </select>
            </div>

            <div class="control-group">
                <label>Timeframe</label>
                <select id="fakeoutTimeframeFilter">
                    <option value="">All Timeframes</option>
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1d">1 Day</option>
                </select>
            </div>

            <div class="control-group">
                <label>Type</label>
                <select id="fakeoutTypeFilter">
                    <option value="">All Types</option>
                    <option value="high">High Fakeout</option>
                    <option value="low">Low Fakeout</option>
                </select>
            </div>

            <button id="loadFakeoutsBtn">Load Fakeouts</button>
            <button class="secondary" id="clearFakeoutFiltersBtn">Clear Filters</button>
        </div>

        <div id="fakeoutInfo" class="info" style="display:none">
            <div id="fakeoutInfoText"></div>
        </div>

        <div id="fakeoutError" class="error" style="display:none"></div>

        <div id="fakeoutContent">
            <div class="empty">
                <p>👆 Click "Load Fakeouts" to view detected fakeouts</p>
            </div>
        </div>

        <div id="fakeoutPagination" class="pagination" style="display:none">
            <button id="fakeoutPrevBtn">← Previous</button>
            <span>Page <span id="fakeoutCurrentPage">1</span> of <span id="fakeoutTotalPages">1</span></span>
            <button id="fakeoutNextBtn">Next →</button>
        </div>
    `;

    document.getElementById('loadFakeoutsBtn').onclick = loadFakeouts;
    document.getElementById('clearFakeoutFiltersBtn').onclick = clearFakeoutFilters;
    document.getElementById('fakeoutSymbolFilter').onchange = applyFakeoutFilters;
    document.getElementById('fakeoutTimeframeFilter').onchange = applyFakeoutFilters;
    document.getElementById('fakeoutTypeFilter').onchange = applyFakeoutFilters;
    document.getElementById('fakeoutPrevBtn').onclick = prevFakeoutPage;
    document.getElementById('fakeoutNextBtn').onclick = nextFakeoutPage;

    loadFakeoutStats();
    loadFakeouts();
}

async function loadFakeoutStats() {
    try {
        const r = await fetch(`${API}/fakeouts/stats`);
        const s = await r.json();
        statToday.textContent = s.today || 0;
        statWeek.textContent = s.week || 0;
        statMonth.textContent = s.month || 0;
    } catch {}
}

async function loadFakeouts() {
    const btn = loadFakeoutsBtn;
    btn.disabled = true;
    btn.textContent = 'Loading...';

    try {
        const r = await fetch(`${API}/fakeouts?limit=200`);
        const d = await r.json();
        allFakeouts = d.fakeouts || [];
        applyFakeoutFilters();
    } catch (e) {
        fakeoutError.textContent = e.message;
        fakeoutError.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Load Fakeouts';
    }
}

function applyFakeoutFilters() {
    filteredFakeouts = allFakeouts.filter(f => {
        if (fakeoutSymbolFilter.value && f.symbol !== fakeoutSymbolFilter.value) return false;
        if (fakeoutTimeframeFilter.value && f.timeframe !== fakeoutTimeframeFilter.value) return false;
        if (fakeoutTypeFilter.value && f.fakeout_type !== fakeoutTypeFilter.value) return false;
        return true;
    }).sort((a,b)=>new Date(b.timestamp)-new Date(a.timestamp));

    fakeoutInfo.style.display = 'block';
    fakeoutInfoText.textContent = `Found ${filteredFakeouts.length} fakeouts`;

    currentFakeoutPage = 1;
    displayFakeoutPage();
}

function displayFakeoutPage() {
    const totalPages = Math.ceil(filteredFakeouts.length / fakeoutsPerPage);
    fakeoutCurrentPage.textContent = currentFakeoutPage;
    fakeoutTotalPages.textContent = totalPages;
    fakeoutPagination.style.display = totalPages > 1 ? 'flex' : 'none';

    renderFakeoutCards(
        filteredFakeouts.slice(
            (currentFakeoutPage - 1) * fakeoutsPerPage,
            currentFakeoutPage * fakeoutsPerPage
        )
    );
}

function renderFakeoutCards(list) {
    fakeoutContent.innerHTML = `
        <div class="fakeouts-grid">
            ${list.map(f=>`
                <div class="fakeout-card ${f.fakeout_type}" onclick='showFakeoutDetail(${JSON.stringify(f)})'>
                    <strong>${f.symbol.toUpperCase()}</strong> ${f.timeframe}
                    <div>${formatDateTime(f.timestamp)}</div>
                </div>
            `).join('')}
        </div>
    `;
}

async function showFakeoutDetail(f) {
    app.innerHTML = `
        <button class="back-button" onclick="loadFakeoutsPage(app)">← Back</button>
        <h1>${f.symbol.toUpperCase()} ${f.timeframe}</h1>
        <canvas id="contextCanvas"></canvas>
    `;
    loadContextChart(f);
}

async function loadContextChart(f) {
    const r = await fetch(`${API}/fakeouts/${f.id}?symbol=${f.symbol}&timeframe=${f.timeframe}`);
    const d = await r.json();
    renderContextChart(f, d.context_candles || []);
}

function renderContextChart(f, candles) {
    const ctx = contextCanvas.getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: candles.map(c=>formatTime(c.timestamp)),
            datasets: [{
                label: 'Close',
                data: candles.map(c=>+c.close),
                borderWidth: 2,
                fill: false
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: c => `${c.dataset.label}: ${c.parsed.y.toFixed(2)}`
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
    fakeoutSymbolFilter.value = '';
    fakeoutTimeframeFilter.value = '';
    fakeoutTypeFilter.value = '';
    applyFakeoutFilters();
}

function formatPrice(v) {
    return v == null ? 'N/A' : `$${(+v).toFixed(2)}`;
}

function formatDateTime(ts) {
    return new Date(ts).toLocaleString();
}

function formatTime(ts) {
    return new Date(ts).toLocaleTimeString();
}
