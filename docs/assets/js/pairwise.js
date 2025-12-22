// JavaScript for the pairwise results page

document.addEventListener('DOMContentLoaded', function() {
    initializePairwisePage();
});

function initializePairwisePage() {
    try {
        populatePairwiseMatrix();
        populateDetailedResults();
        setupFilters();
        setupMetricSelector();
        setLastUpdated();
    } catch (error) {
        console.error('Error initializing pairwise page:', error);
        showError('Failed to load pairwise data');
    }
}

function populatePairwiseMatrix() {
    const pairwiseData = getPairwiseResults();
    const llms = Object.keys(pairwiseData);
    
    createMatrixTable(llms, pairwiseData);
}

function createMatrixTable(llms, data) {
    const table = document.getElementById('pairwise-table');
    const header = document.getElementById('matrix-header');
    const body = document.getElementById('matrix-body');
    
    if (!table || !header || !body) {
        console.error('Matrix table elements not found');
        return;
    }
    
    // Create header
    header.innerHTML = '';
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th>LLM</th>';
    
    llms.forEach(llm => {
        const th = document.createElement('th');
        th.textContent = llm;
        th.title = `vs ${llm}`;
        headerRow.appendChild(th);
    });
    
    header.appendChild(headerRow);
    
    // Create body
    body.innerHTML = '';
    
    llms.forEach(rowLLM => {
        const row = document.createElement('tr');
        
        // Row header
        const rowHeader = document.createElement('td');
        rowHeader.textContent = rowLLM;
        rowHeader.className = 'row-header';
        row.appendChild(rowHeader);
        
        // Data cells
        llms.forEach(colLLM => {
            const cell = document.createElement('td');
            
            if (rowLLM === colLLM) {
                cell.textContent = '-';
                cell.className = 'matrix-cell neutral';
            } else if (data[rowLLM] && data[rowLLM][colLLM]) {
                const result = data[rowLLM][colLLM];
                const metric = getSelectedMetric();
                const value = getMetricValue(result, metric);
                
                cell.innerHTML = formatMatrixValue(value, metric);
                cell.className = `matrix-cell ${getPerformanceClass(value)}`;
                cell.title = `${rowLLM} vs ${colLLM}: ${formatMatrixTooltip(result)}`;
            } else {
                cell.textContent = 'N/A';
                cell.className = 'matrix-cell neutral';
            }
            
            row.appendChild(cell);
        });
        
        body.appendChild(row);
    });
}

function getSelectedMetric() {
    const select = document.getElementById('metric-select');
    return select ? select.value : 'winnings';
}

function getMetricValue(result, metric) {
    switch (metric) {
        case 'winnings':
            return result.avgWinnings;
        case 'winrate':
            return result.winRate;
        case 'sessions':
            return result.sessions;
        default:
            return result.avgWinnings;
    }
}

function formatMatrixValue(value, metric) {
    switch (metric) {
        case 'winnings':
            return formatNumber(value, 1);
        case 'winrate':
            return value.toFixed(1) + '%';
        case 'sessions':
            return value.toString();
        default:
            return value.toFixed(2);
    }
}

function formatMatrixTooltip(result) {
    return `Avg: ${formatNumber(result.avgWinnings)}, Win Rate: ${result.winRate.toFixed(1)}%, Sessions: ${result.sessions}, Hands: ${result.totalHands}`;
}

function populateDetailedResults() {
    const pairwiseData = getPairwiseResults();
    const container = document.getElementById('detailed-results-container');
    
    if (!container) {
        console.error('Detailed results container not found');
        return;
    }
    
    container.innerHTML = '';
    
    // Create detailed results list
    const results = [];
    
    Object.keys(pairwiseData).forEach(llm1 => {
        Object.keys(pairwiseData[llm1]).forEach(llm2 => {
            const result = pairwiseData[llm1][llm2];
            results.push({
                llm1,
                llm2,
                ...result
            });
        });
    });
    
    // Sort by most recent or most significant results
    results.sort((a, b) => b.avgWinnings - a.avgWinnings);
    
    results.forEach(result => {
        const resultCard = document.createElement('div');
        resultCard.className = 'match-card';
        
        resultCard.innerHTML = `
            <div class="match-header">
                <div class="match-title">${result.llm1} vs ${result.llm2}</div>
                <div class="match-date">${result.sessions} session(s)</div>
            </div>
            <div class="match-stats">
                <div class="match-stat">
                    <div class="match-stat-value ${getPerformanceClass(result.avgWinnings)}">${formatNumber(result.avgWinnings)}</div>
                    <div class="match-stat-label">Avg Chips/Hand</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value ${getPerformanceClass(result.winRate - 50)}">${result.winRate.toFixed(1)}%</div>
                    <div class="match-stat-label">Win Rate</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value">${result.totalHands}</div>
                    <div class="match-stat-label">Total Hands</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value ${getFallbackClass((result.fallbacks / result.totalHands) * 100)}">${result.fallbacks}</div>
                    <div class="match-stat-label">Fallbacks</div>
                </div>
            </div>
        `;
        
        container.appendChild(resultCard);
    });
}

function setupFilters() {
    const pairwiseData = getPairwiseResults();
    const llms = Object.keys(pairwiseData);
    
    // Populate LLM filters
    const llmFilter = document.getElementById('llm-filter');
    const opponentFilter = document.getElementById('opponent-filter');
    
    if (llmFilter && opponentFilter) {
        llms.forEach(llm => {
            const option1 = document.createElement('option');
            option1.value = llm;
            option1.textContent = llm;
            llmFilter.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = llm;
            option2.textContent = llm;
            opponentFilter.appendChild(option2);
        });
        
        // Add filter event listeners
        llmFilter.addEventListener('change', applyFilters);
        opponentFilter.addEventListener('change', applyFilters);
    }
}

function setupMetricSelector() {
    const metricSelect = document.getElementById('metric-select');
    if (metricSelect) {
        metricSelect.addEventListener('change', function() {
            populatePairwiseMatrix();
        });
    }
}

function applyFilters() {
    const llmFilter = document.getElementById('llm-filter').value;
    const opponentFilter = document.getElementById('opponent-filter').value;
    
    const resultCards = document.querySelectorAll('#detailed-results-container .match-card');
    
    resultCards.forEach(card => {
        const title = card.querySelector('.match-title').textContent;
        const [llm1, llm2] = title.split(' vs ');
        
        let show = true;
        
        if (llmFilter && llm1 !== llmFilter && llm2 !== llmFilter) {
            show = false;
        }
        
        if (opponentFilter && llm1 !== opponentFilter && llm2 !== opponentFilter) {
            show = false;
        }
        
        // Don't show if both filters are the same LLM (would be self-match)
        if (llmFilter && opponentFilter && llmFilter === opponentFilter) {
            show = false;
        }
        
        card.style.display = show ? 'block' : 'none';
    });
}

function setLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement && window.benchmarkData.lastUpdated) {
        lastUpdatedElement.textContent = formatDate(window.benchmarkData.lastUpdated);
    }
}

function showError(message) {
    const main = document.querySelector('main');
    if (main) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Error:</strong> ${message}
        `;
        main.insertBefore(errorDiv, main.firstChild);
    }
}

// Add matrix cell click handlers for detailed view
document.addEventListener('DOMContentLoaded', function() {
    const matrixTable = document.getElementById('pairwise-table');
    if (matrixTable) {
        matrixTable.addEventListener('click', function(e) {
            const cell = e.target.closest('td');
            if (cell && cell.title && !cell.classList.contains('row-header')) {
                // Future: Show detailed popup for this matchup
                console.log('Clicked on matchup:', cell.title);
            }
        });
    }
});
