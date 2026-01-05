// Fakeouts Page Logic
const API = '/api';
let allFakeouts = [];
let filteredFakeouts = [];
let currentFakeoutPage = 1;
let fakeoutsPerPage = 12;
let selectedFakeout = null;

function loadFakeoutsPage(container) {
    container.innerHTML = `
        <h1 class="page-title">Fakeouts Detector</h1>

        <!-- Stats Cards -->
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

        <!-- Filters -->
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

        <!-- Info -->
        <div id="fakeoutInfo" class="info" style="display: none;">
            <div class="info-text" id="fakeoutInfoText"></div>
        </div>

        <!-- Error -->
        <div id="fakeoutError" class="error" style="display: none;"></div>

        <!-- Main Content Area -->
        <div id="fakeoutContent">
            <div class="empty">
                <p>👆 Click "Load Fakeouts" to view detected fakeouts</p>
            </div>
        </div>

        <!-- Pagination -->
        <div id="fakeoutPagination" class="pagination" style="display: none;">
            <button id="fakeoutPrevBtn">← Previous</button>
            <div class="page-info">
                Page <span id="fakeoutCurrentPage">1</span> of <span id="fakeoutTotalPages">1</span>
            </div>
            <button id="fakeoutNextBtn">Next →</button>
        </div>
    `;

    // Attach event listeners
    document.getElementById('loadFakeoutsBtn').addEventListener('click', loadFakeouts);
    document.getElementById('clearFakeoutFiltersBtn').addEventListener('click', clearFakeoutFilters);
    document.getElementById('fakeoutSymbolFilter').addEventListener('change', applyFakeoutFilters);
    document.getElementById('fakeoutTimeframeFilter').addEventListener('change', applyFakeoutFilters);
    document.getElementById('fakeoutTypeFilter').addEventListener('change', applyFakeoutFilters);
    document.getElementById('fakeoutPrevBtn').addEventListener('click', prevFakeoutPage);
    document.getElementById('fakeoutNextBtn').addEventListener('click', nextFakeoutPage);

    // Auto-load stats and fakeouts
    loadFakeoutStats();
    loadFakeouts();
}

async function loadFakeoutStats() {
    try {
        const response = await fetch(`${API}/fakeouts/stats`);
        if (!response.ok) throw new Error('Failed to load stats');
        
        const stats = await response.json();
        document.getElementById('statToday').textContent = stats.today || 0;
        document.getElementById('statWeek').textContent = stats.week || 0;
        document.getElementById('statMonth').textContent = stats.month || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadFakeouts() {
    const loadBtn = document.getElementById('loadFakeoutsBtn');
    const errorDiv = document.getElementById('fakeoutError');
    const infoDiv = document.getElementById('fakeoutInfo');
    const content = document.getElementById('fakeoutContent');

    errorDiv.style.display = 'none';
    infoDiv.style.display = 'none';
    document.getElementById('fakeoutPagination').style.display = 'none';
    loadBtn.disabled = true;
    loadBtn.textContent = 'Loading...';

    content.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading fakeouts...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API}/fakeouts?limit=200`);
        if (!response.ok) throw new Error(`Server returned ${response.status}`);

        const data = await response.json();
        allFakeouts = data.fakeouts || [];

        if (allFakeouts.length === 0) {
            content.innerHTML = '<div class="empty"><p>No fakeouts detected yet</p></div>';
            return;
        }

        applyFakeoutFilters();

    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = `Error loading fakeouts: ${error.message}`;
        errorDiv.style.display = 'block';
        content.innerHTML = '<div class="empty"><p>Failed to load fakeouts</p></div>';
    } finally {
        loadBtn.disabled = false;
        loadBtn.textContent = 'Load Fakeouts';
    }
}

function applyFakeoutFilters() {
    const symbolFilter = document.getElementById('fakeoutSymbolFilter').value;
    const timeframeFilter = document.getElementById('fakeoutTimeframeFilter').value;
    const typeFilter = document.getElementById('fakeoutTypeFilter').value;

    filteredFakeouts = allFakeouts.filter(f => {
        if (symbolFilter && f.symbol !== symbolFilter) return false;
        if (timeframeFilter && f.timeframe !== timeframeFilter) return false;
        if (typeFilter && f.fakeout_type !== typeFilter) return false;
        return true;
    });

    // Sort by timestamp descending (newest first)
    filteredFakeouts.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    const infoDiv = document.getElementById('fakeoutInfo');
    infoDiv.style.display = 'flex';
    document.getElementById('fakeoutInfoText').textContent = 
        `Found ${filteredFakeouts.length} fakeouts`;

    currentFakeoutPage = 1;
    displayFakeoutPage();
}

function displayFakeoutPage() {
    const totalPages = Math.ceil(filteredFakeouts.length / fakeoutsPerPage);
    const startIdx = (currentFakeoutPage - 1) * fakeoutsPerPage;
    const endIdx = startIdx + fakeoutsPerPage;
    const pageFakeouts = filteredFakeouts.slice(startIdx, endIdx);

    // Update pagination
    document.getElementById('fakeoutCurrentPage').textContent = currentFakeoutPage;
    document.getElementById('fakeoutTotalPages').textContent = totalPages;
    document.getElementById('fakeoutPrevBtn').disabled = currentFakeoutPage === 1;
    document.getElementById('fakeoutNextBtn').disabled = currentFakeoutPage === totalPages;

    if (totalPages > 1) {
        document.getElementById('fakeoutPagination').style.display = 'flex';
    } else {
        document.getElementById('fakeoutPagination').style.display = 'none';
    }

    renderFakeoutCards(pageFakeouts);
}

function renderFakeoutCards(fakeouts) {
    const content = document.getElementById('fakeoutContent');
    
    if (fakeouts.length === 0) {
        content.innerHTML = '<div class="empty"><p>No fakeouts match your filters</p></div>';
        return;
    }

    const cardsHTML = fakeouts.map(f => {
        const isHigh = f.fakeout_type === 'high';
        const typeClass = isHigh ? 'high' : 'low';
        const typeIcon = isHigh ? '🔴' : '🟢';
        
        return `
            <div class="fakeout-card ${typeClass}" onclick='showFakeoutDetail(${JSON.stringify(f).replace(/'/g, "&#39;")})'>
                <div class="fakeout-card-header">
                    <div class="fakeout-symbol">
                        <span class="symbol-text">${f.symbol.toUpperCase()}</span>
                        <span class="timeframe-badge">${f.timeframe}</span>
                    </div>
                    <div class="fakeout-type-badge ${typeClass}">
                        ${typeIcon} ${f.fakeout_type.toUpperCase()}
                    </div>
                </div>
                <div class="fakeout-card-body">
                    <div class="fakeout-data-row">
                        <span class="data-label">Fakeout Level:</span>
                        <span class="data-value">${formatPrice(f.fakeout_level)}</span>
                    </div>
                    <div class="fakeout-data-row">
                        <span class="data-label">Close:</span>
                        <span class="data-value">${formatPrice(f.close)}</span>
                    </div>
                    <div class="fakeout-data-grid">
                        <div class="fakeout-data-row">
                            <span class="data-label">High:</span>
                            <span class="data-value">${formatPrice(f.high)}</span>
                        </div>
                        <div class="fakeout-data-row">
                            <span class="data-label">Low:</span>
                            <span class="data-value">${formatPrice(f.low)}</span>
                        </div>
                    </div>
                    <div class="fakeout-data-row">
                        <span class="data-label">RSI:</span>
                        <span class="data-value">${f.rsi_8 ? parseFloat(f.rsi_8).toFixed(1) : 'N/A'}</span>
                    </div>
                </div>
                <div class="fakeout-card-footer">
                    <span class="timestamp">${formatDateTime(f.timestamp)}</span>
                </div>
            </div>
        `;
    }).join('');

    content.innerHTML = `<div class="fakeouts-grid">${cardsHTML}</div>`;
}

async function showFakeoutDetail(fakeout) {
    const container = document.getElementById('app');
    
    container.innerHTML = `
        <button class="back-button" id="backToFakeoutsBtn">← Back to Fakeouts</button>
        
        <div class="fakeout-detail">
            <div class="fakeout-detail-header">
                <div>
                    <h1 class="page-title">${fakeout.symbol.toUpperCase()} - ${fakeout.timeframe}</h1>
                    <p class="detail-subtitle">${formatDateTime(fakeout.timestamp)}</p>
                </div>
                <div class="fakeout-type-badge ${fakeout.fakeout_type} large">
                    ${fakeout.fakeout_type === 'high' ? '🔴' : '🟢'} ${fakeout.fakeout_type.toUpperCase()} FAKEOUT
                </div>
            </div>

            <div class="detail-stats-grid">
                <div class="detail-stat">
                    <span class="detail-stat-label">Fakeout Level</span>
                    <span class="detail-stat-value">${formatPrice(fakeout.fakeout_level)}</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-label">Open</span>
                    <span class="detail-stat-value">${formatPrice(fakeout.open)}</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-label">High</span>
                    <span class="detail-stat-value">${formatPrice(fakeout.high)}</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-label">Low</span>
                    <span class="detail-stat-value">${formatPrice(fakeout.low)}</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-label">Close</span>
                    <span class="detail-stat-value">${formatPrice(fakeout.close)}</span>
                </div>
                <div class="detail-stat">
                    <span class="detail-stat-label">RSI (8)</span>
                    <span class="detail-stat-value">${fakeout.rsi_8 ? parseFloat(fakeout.rsi_8).toFixed(1) : 'N/A'}</span>
                </div>
            </div>

            <div class="chart-section">
                <h2 class="section-title">Context Chart</h2>
                <div id="contextChartContainer">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Loading context candles...</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Back button handler
    document.getElementById('backToFakeoutsBtn').addEventListener('click', () => {
        loadFakeoutsPage(container);
    });

    // Load context chart
    loadContextChart(fakeout);
}

async function loadContextChart(fakeout) {
    const chartContainer = document.getElementById('contextChartContainer');

    try {
        const response = await fetch(
            `${API}/fakeouts/${fakeout.id}?symbol=${fakeout.symbol}&timeframe=${fakeout.timeframe}`
        );
        
        if (!response.ok) throw new Error('Failed to load context');

        const data = await response.json();
        const contextCandles = data.context_candles;

        if (!contextCandles || contextCandles.length === 0) {
            chartContainer.innerHTML = `
                <div class="empty">
                    <p>No context candles available for ${fakeout.timeframe} timeframe</p>
                    ${fakeout.timeframe === '4h' ? '<p class="text-sm">(4h fakeouts have no context by design)</p>' : ''}
                </div>
            `;
            return;
        }

        renderContextChart(fakeout, contextCandles);

    } catch (error) {
        console.error('Error loading context:', error);
        chartContainer.innerHTML = `
            <div class="error">
                Failed to load context chart: ${error.message}
            </div>
        `;
    }
}

function renderContextChart(fakeout, candles) {
    const chartContainer = document.getElementById('contextChartContainer');
    
    // Create simple ASCII-style chart (you can replace with Chart.js later)
    const contextInfo = fakeout.timeframe === '1h' 
        ? '5m candles: 1 hour before + 2 hours after'
        : '1h candles: 24 hours before + 24 hours after';

    const tableHTML = `
        <div class="context-info">${contextInfo}</div>
        <div class="context-table-container">
            <table class="context-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                    </tr>
                </thead>
                <tbody>
                    ${candles.map(c => `
                        <tr>
                            <td class="timestamp">${formatTime(c.timestamp)}</td>
                            <td>${formatPrice(c.open)}</td>
                            <td>${formatPrice(c.high)}</td>
                            <td>${formatPrice(c.low)}</td>
                            <td class="${parseFloat(c.close) >= parseFloat(c.open) ? 'positive' : 'negative'}">
                                ${formatPrice(c.close)}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="chart-note">
            <strong>Fakeout Level:</strong> ${formatPrice(fakeout.fakeout_level)} 
            (${fakeout.fakeout_type === 'high' ? 'Price spiked above then closed below' : 'Price dipped below then closed above'})
        </div>
    `;

    chartContainer.innerHTML = tableHTML;
}

function nextFakeoutPage() {
    const totalPages = Math.ceil(filteredFakeouts.length / fakeoutsPerPage);
    if (currentFakeoutPage < totalPages) {
        currentFakeoutPage++;
        displayFakeoutPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function prevFakeoutPage() {
    if (currentFakeoutPage > 1) {
        currentFakeoutPage--;
        displayFakeoutPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function clearFakeoutFilters() {
    document.getElementById('fakeoutSymbolFilter').value = '';
    document.getElementById('fakeoutTimeframeFilter').value = '';
    document.getElementById('fakeoutTypeFilter').value = '';
    applyFakeoutFilters();
}

// Utility functions
function formatPrice(value) {
    if (value === null || value === undefined) return 'N/A';
    return '$' + parseFloat(value).toFixed(2);
}

function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}