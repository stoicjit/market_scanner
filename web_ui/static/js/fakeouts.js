// Fakeouts Page Logic
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
    
    const contextInfo = fakeout.timeframe === '1h' 
        ? '5m candles: 1 hour before + 2 hours after'
        : '1h candles: 24 hours before + 24 hours after';

    chartContainer.innerHTML = `
        <div class="context-info">${contextInfo}</div>
        <div class="chart-canvas-container">
            <canvas id="contextCanvas"></canvas>
        </div>
        <div class="chart-note">
            <strong>Fakeout Level:</strong> ${formatPrice(fakeout.fakeout_level)} 
            (${fakeout.fakeout_type === 'high' ? 'Price spiked above then closed below' : 'Price dipped below then closed above'})
        </div>
    `;

    // Prepare chart data
    const labels = candles.map(c => formatTime(c.timestamp));
    const closes = candles.map(c => parseFloat(c.close));
    const highs = candles.map(c => parseFloat(c.high));
    const lows = candles.map(c => parseFloat(c.low));
    const fakeoutLevel = parseFloat(fakeout.fakeout_level);

    // Create chart
    const ctx = document.getElementById('contextCanvas').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Close',
                    data: closes,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 4,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'High',
                    data: highs,
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    borderDash: [5, 5]
                },
                {
                    label: 'Low',
                    data: lows,
                    borderColor: '#10b981',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                    borderDash: [5, 5]
                },
                {
                    label: 'Fakeout Level',
                    data: Array(candles.length).fill(fakeoutLevel),
                    borderColor: fakeout.fakeout_type === 'high' ? '#f59e0b' : '#8b5cf6',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    borderDash: [10, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        font: {
                            size: 12
                        },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#e2e8f0',
                    bodyColor: '#94a3b8',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += "'"

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
} + context.parsed.y.toFixed(2);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            size: 10
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: '#334155',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            size: 11
                        },
                        callback: function(value) {
                            return "'"

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
} + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
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