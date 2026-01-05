// Candles Page Logic
const API = '/api';
let allCandles = [];
let filteredCandles = [];
let currentPage = 1;
let sortOrder = 'desc';

function loadCandlesPage(container) {
    container.innerHTML = `
        <h1 class="page-title">Candles Table Viewer</h1>

        <!-- Controls -->
        <div class="controls">
            <div class="control-group">
                <label>Symbol</label>
                <select id="symbolSelect">
                    <option value="">-- Select Symbol --</option>
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
                <select id="timeframeSelect">
                    <option value="">-- Select Timeframe --</option>
                    <option value="5m">5 Minutes</option>
                    <option value="1h">1 Hour</option>
                    <option value="4h">4 Hours</option>
                    <option value="1d">1 Day</option>
                    <option value="1w">1 Week</option>
                    <option value="1M">1 Month</option>
                </select>
            </div>

            <div class="control-group">
                <label>Rows to Show</label>
                <select id="limitSelect">
                    <option value="20">20</option>
                    <option value="50" selected>50</option>
                    <option value="100">100</option>
                </select>
            </div>

            <button id="loadBtn">Load Data</button>

            <!-- Date Filter Row -->
            <div class="filters-row">
                <div class="control-group">
                    <label>Start Date/Time (Optional)</label>
                    <input type="datetime-local" id="startDate">
                </div>

                <div class="control-group">
                    <label>End Date/Time (Optional)</label>
                    <input type="datetime-local" id="endDate">
                </div>

                <button class="secondary" id="clearFiltersBtn">Clear Filters</button>
            </div>
        </div>

        <!-- Info Display -->
        <div id="info" class="info" style="display: none;">
            <div class="info-text" id="infoText"></div>
            <div class="sort-control">
                <span style="color: #94a3b8; font-size: 13px;">Sort:</span>
                <button id="sortNewBtn" class="active">New → Old</button>
                <button id="sortOldBtn">Old → New</button>
            </div>
        </div>

        <!-- Error Display -->
        <div id="error" class="error" style="display: none;"></div>

        <!-- Table -->
        <div class="table-container">
            <div id="tableContent">
                <div class="empty">
                    <p>👆 Select a symbol and timeframe to view candles</p>
                </div>
            </div>
        </div>

        <!-- Pagination -->
        <div id="pagination" class="pagination" style="display: none;">
            <button id="prevBtn">← Previous</button>
            <div class="page-info">
                Page <span id="currentPage">1</span> of <span id="totalPages">1</span>
            </div>
            <button id="nextBtn">Next →</button>
        </div>
    `;

    // Attach event listeners
    document.getElementById('loadBtn').addEventListener('click', loadCandles);
    document.getElementById('clearFiltersBtn').addEventListener('click', clearFilters);
    document.getElementById('sortNewBtn').addEventListener('click', () => setSortOrder('desc'));
    document.getElementById('sortOldBtn').addEventListener('click', () => setSortOrder('asc'));
    document.getElementById('prevBtn').addEventListener('click', prevPage);
    document.getElementById('nextBtn').addEventListener('click', nextPage);
    
    // Enter key to load
    document.getElementById('timeframeSelect').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadCandles();
    });
}

async function loadCandles() {
    const symbol = document.getElementById('symbolSelect').value;
    const timeframe = document.getElementById('timeframeSelect').value;
    const limit = parseInt(document.getElementById('limitSelect').value);
    const loadBtn = document.getElementById('loadBtn');
    const errorDiv = document.getElementById('error');
    const infoDiv = document.getElementById('info');
    const tableContent = document.getElementById('tableContent');

    // Validation
    if (!symbol || !timeframe) {
        errorDiv.textContent = 'Please select both symbol and timeframe';
        errorDiv.style.display = 'block';
        return;
    }

    // Hide error, show loading
    errorDiv.style.display = 'none';
    infoDiv.style.display = 'none';
    document.getElementById('pagination').style.display = 'none';
    loadBtn.disabled = true;
    loadBtn.textContent = 'Loading...';

    tableContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading candles...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API}/candles/${symbol}/${timeframe}?limit=${limit}`);
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();
        
        if (!data.candles || data.candles.length === 0) {
            tableContent.innerHTML = `
                <div class="empty">
                    <p>No candles found for ${symbol.toUpperCase()} ${timeframe}</p>
                </div>
            `;
            return;
        }

        // Store all candles
        allCandles = data.candles;
        
        // Apply date filters
        filterAndDisplay();

    } catch (error) {
        console.error('Error:', error);
        errorDiv.textContent = `Error loading data: ${error.message}`;
        errorDiv.style.display = 'block';
        tableContent.innerHTML = `
            <div class="empty">
                <p>Failed to load data</p>
            </div>
        `;
    } finally {
        loadBtn.disabled = false;
        loadBtn.textContent = 'Load Data';
    }
}

function filterAndDisplay() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    filteredCandles = [...allCandles];

    // Apply date filters
    if (startDate) {
        const startTime = new Date(startDate).getTime();
        filteredCandles = filteredCandles.filter(c => new Date(c.timestamp).getTime() >= startTime);
    }

    if (endDate) {
        const endTime = new Date(endDate).getTime();
        filteredCandles = filteredCandles.filter(c => new Date(c.timestamp).getTime() <= endTime);
    }

    // Apply sort order
    filteredCandles.sort((a, b) => {
        const timeA = new Date(a.timestamp).getTime();
        const timeB = new Date(b.timestamp).getTime();
        return sortOrder === 'desc' ? timeB - timeA : timeA - timeB;
    });

    // Update UI
    const symbol = document.getElementById('symbolSelect').value;
    const timeframe = document.getElementById('timeframeSelect').value;
    const infoDiv = document.getElementById('info');
    
    infoDiv.style.display = 'flex';
    document.getElementById('infoText').textContent = 
        `Showing ${filteredCandles.length} candles for ${symbol.toUpperCase()} - ${timeframe}`;

    // Reset to page 1
    currentPage = 1;
    displayPage();
}

function displayPage() {
    const rowsPerPage = parseInt(document.getElementById('limitSelect').value);
    const totalPages = Math.ceil(filteredCandles.length / rowsPerPage);
    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = startIdx + rowsPerPage;
    const pageCandles = filteredCandles.slice(startIdx, endIdx);

    // Update pagination
    document.getElementById('currentPage').textContent = currentPage;
    document.getElementById('totalPages').textContent = totalPages;
    document.getElementById('prevBtn').disabled = currentPage === 1;
    document.getElementById('nextBtn').disabled = currentPage === totalPages;

    // Show pagination only if needed
    if (totalPages > 1) {
        document.getElementById('pagination').style.display = 'flex';
    } else {
        document.getElementById('pagination').style.display = 'none';
    }

    // Render table
    renderTable(pageCandles);
}

function nextPage() {
    const rowsPerPage = parseInt(document.getElementById('limitSelect').value);
    const totalPages = Math.ceil(filteredCandles.length / rowsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayPage();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        displayPage();
    }
}

function setSortOrder(order) {
    sortOrder = order;
    
    // Update button states
    document.getElementById('sortNewBtn').classList.toggle('active', order === 'desc');
    document.getElementById('sortOldBtn').classList.toggle('active', order === 'asc');
    
    // Re-display with new sort
    filterAndDisplay();
}

function clearFilters() {
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    filterAndDisplay();
}

function renderTable(candles) {
    const tableContent = document.getElementById('tableContent');
    
    const html = `
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                    <th>RSI (8)</th>
                </tr>
            </thead>
            <tbody>
                ${candles.map(candle => {
                    const isGreen = parseFloat(candle.close) >= parseFloat(candle.open);
                    const closeClass = isGreen ? 'positive' : 'negative';
                    
                    return `
                        <tr>
                            <td class="timestamp">${formatTimestamp(candle.timestamp)}</td>
                            <td>${formatNumber(candle.open)}</td>
                            <td>${formatNumber(candle.high)}</td>
                            <td>${formatNumber(candle.low)}</td>
                            <td class="${closeClass}">${formatNumber(candle.close)}</td>
                            <td>${formatVolume(candle.volume)}</td>
                            <td>${formatNumber(candle.rsi_8, 1)}</td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    tableContent.innerHTML = html;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return 'N/A';
    return parseFloat(value).toFixed(decimals);
}

function formatVolume(value) {
    if (value === null || value === undefined) return 'N/A';
    const num = parseFloat(value);
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}