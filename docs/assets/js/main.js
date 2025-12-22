// Main JavaScript for the leaderboard page

document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

function initializePage() {
    try {
        populateStats();
        populateLeaderboard();
        populateRecentMatches();
        setLastUpdated();
    } catch (error) {
        console.error('Error initializing page:', error);
        showError('Failed to load benchmark data');
    }
}

function populateStats() {
    const stats = getBenchmarkStats();
    
    document.getElementById('total-llms').textContent = stats.totalLLMs;
    document.getElementById('total-sessions').textContent = stats.totalSessions.toLocaleString();
    document.getElementById('total-hands').textContent = stats.totalHands.toLocaleString();
}

function populateLeaderboard() {
    const leaderboard = getLeaderboard();
    const tbody = document.getElementById('leaderboard-body');
    
    if (!tbody) {
        console.error('Leaderboard table body not found');
        return;
    }
    
    tbody.innerHTML = '';
    
    leaderboard.forEach((llm, index) => {
        const row = document.createElement('tr');
        
        // Add rank styling for top 3
        if (index < 3) {
            row.classList.add(`rank-${index + 1}`);
        }
        
        row.innerHTML = `
            <td>${getRankDisplay(llm.rank)}</td>
            <td><strong>${llm.name}</strong></td>
            <td class="${getPerformanceClass(llm.avgPerHand)}">${formatNumber(llm.avgPerHand)}</td>
            <td>${llm.totalHands.toLocaleString()}</td>
            <td>${llm.sessions}</td>
            <td class="${getFallbackClass(llm.fallbackRate)}">${llm.fallbackRate.toFixed(1)}%</td>
            <td class="${getPerformanceClass(llm.winRate - 50)}">${llm.winRate.toFixed(1)}%</td>
        `;
        
        tbody.appendChild(row);
    });
}

function populateRecentMatches() {
    const matches = getRecentMatches();
    const container = document.getElementById('recent-matches-container');
    
    if (!container) {
        console.error('Recent matches container not found');
        return;
    }
    
    container.innerHTML = '';
    
    matches.slice(0, 5).forEach(match => {
        const matchCard = document.createElement('div');
        matchCard.className = 'match-card';
        
        const winnerName = match.llm1Winnings > 0 ? match.llm1 : match.llm2;
        const winnerWinnings = Math.abs(match.llm1Winnings);
        const winningsPerHand = winnerWinnings / match.handsPlayed;
        
        matchCard.innerHTML = `
            <div class="match-header">
                <div class="match-title">${match.llm1} vs ${match.llm2}</div>
                <div class="match-date">${formatDate(match.date)}</div>
            </div>
            <div class="match-stats">
                <div class="match-stat">
                    <div class="match-stat-value">${winnerName}</div>
                    <div class="match-stat-label">Winner</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value">${match.handsPlayed}</div>
                    <div class="match-stat-label">Hands Played</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value">${formatNumber(winningsPerHand)}</div>
                    <div class="match-stat-label">Chips/Hand</div>
                </div>
                <div class="match-stat">
                    <div class="match-stat-value">${match.llm1Fallbacks + match.llm2Fallbacks}</div>
                    <div class="match-stat-label">Total Fallbacks</div>
                </div>
            </div>
        `;
        
        container.appendChild(matchCard);
    });
}

function getRankDisplay(rank) {
    const medals = ['🥇', '🥈', '🥉'];
    if (rank <= 3) {
        return medals[rank - 1];
    }
    return rank.toString();
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

function showLoading() {
    const main = document.querySelector('main');
    if (main) {
        main.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner"></i>
                <p>Loading benchmark data...</p>
            </div>
        `;
    }
}

// Add some interactive features
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for table rows (future enhancement)
    const leaderboardTable = document.getElementById('leaderboard-table');
    if (leaderboardTable) {
        leaderboardTable.addEventListener('click', function(e) {
            const row = e.target.closest('tr');
            if (row && row.querySelector('td')) {
                // Future: Navigate to detailed LLM page
                console.log('Clicked on LLM:', row.querySelector('td:nth-child(2)').textContent);
            }
        });
    }
    
    // Add refresh functionality (future enhancement)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
            // Future: Implement data refresh
            console.log('Refresh requested');
        }
    });
});
