// JavaScript for the hand history page

let currentPage = 1;
let handsPerPage = 20;
let filteredHands = [];
let allHands = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeHandsPage();
});

function initializeHandsPage() {
    try {
        loadHandData();
        setupFilters();
        setupPagination();
        setupModal();
        setLastUpdated();
        displayHands();
        updateStats();
    } catch (error) {
        console.error('Error initializing hands page:', error);
        showError('Failed to load hand history data');
    }
}

function loadHandData() {
    // Get hand data from the global data object
    allHands = window.benchmarkData?.handLogs || [];
    filteredHands = [...allHands];
    
    console.log(`Loaded ${allHands.length} hands`);
}

function setupFilters() {
    const llmFilter = document.getElementById('llm-filter');
    const sessionFilter = document.getElementById('session-filter');
    
    // Populate LLM filter
    const llms = new Set();
    allHands.forEach(hand => {
        llms.add(hand.llm1_name);
        llms.add(hand.llm2_name);
    });
    
    llms.forEach(llm => {
        const option = document.createElement('option');
        option.value = llm;
        option.textContent = llm;
        llmFilter.appendChild(option);
    });
    
    // Populate session filter
    const sessions = new Set();
    allHands.forEach(hand => {
        sessions.add(hand.session_id);
    });
    
    sessions.forEach(sessionId => {
        const option = document.createElement('option');
        option.value = sessionId;
        option.textContent = `Session ${sessionId}`;
        sessionFilter.appendChild(option);
    });
    
    // Add event listeners
    document.getElementById('llm-filter').addEventListener('change', applyFilters);
    document.getElementById('session-filter').addEventListener('change', applyFilters);
    document.getElementById('winner-filter').addEventListener('change', applyFilters);
    document.getElementById('showdown-filter').addEventListener('change', applyFilters);
    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('search-btn').addEventListener('click', applyFilters);
}

function setupPagination() {
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            displayHands();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = Math.ceil(filteredHands.length / handsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            displayHands();
        }
    });
}

function setupModal() {
    const modal = document.getElementById('hand-modal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

function applyFilters() {
    const llmFilter = document.getElementById('llm-filter').value;
    const sessionFilter = document.getElementById('session-filter').value;
    const winnerFilter = document.getElementById('winner-filter').value;
    const showdownFilter = document.getElementById('showdown-filter').value;
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    
    filteredHands = allHands.filter(hand => {
        // LLM filter
        if (llmFilter && hand.llm1_name !== llmFilter && hand.llm2_name !== llmFilter) {
            return false;
        }
        
        // Session filter
        if (sessionFilter && hand.session_id.toString() !== sessionFilter) {
            return false;
        }
        
        // Winner filter
        if (winnerFilter && hand.winner !== winnerFilter) {
            return false;
        }
        
        // Showdown filter
        if (showdownFilter !== '') {
            const isShowdown = showdownFilter === 'true';
            if (hand.showdown !== isShowdown) {
                return false;
            }
        }
        
        // Search filter
        if (searchTerm) {
            const searchableText = [
                hand.llm1_name,
                hand.llm2_name,
                hand.hand_strength_llm1,
                hand.hand_strength_llm2,
                JSON.stringify(hand.actions)
            ].join(' ').toLowerCase();
            
            if (!searchableText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    currentPage = 1;
    displayHands();
    updateStats();
}

function displayHands() {
    const container = document.getElementById('hands-container');
    const startIndex = (currentPage - 1) * handsPerPage;
    const endIndex = startIndex + handsPerPage;
    const handsToShow = filteredHands.slice(startIndex, endIndex);
    
    if (handsToShow.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <h3>No hands found</h3>
                <p>Try adjusting your filters or search terms.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    handsToShow.forEach(hand => {
        const handCard = createHandCard(hand);
        container.appendChild(handCard);
    });
    
    updatePagination();
}

function createHandCard(hand) {
    const card = document.createElement('div');
    card.className = 'hand-card';
    card.addEventListener('click', () => showHandDetails(hand));
    
    const winner = hand.winner;
    const winnerClass = winner === 'llm1' ? 'winner' : winner === 'llm2' ? 'winner' : '';
    
    // Parse actions to count fallbacks
    let actions = [];
    try {
        actions = JSON.parse(hand.actions);
    } catch (e) {
        actions = [];
    }
    
    const fallbackCount = actions.filter(action => action.is_fallback).length;
    const totalActions = actions.length;
    
    card.innerHTML = `
        <div class="hand-header">
            <div class="hand-title">${hand.llm1_name} vs ${hand.llm2_name}</div>
            <div class="hand-number">Hand #${hand.hand_number}</div>
        </div>
        
        <div class="hand-players">
            <div class="player-info ${winner === 'llm1' ? 'winner' : winner === 'llm2' ? 'loser' : ''}">
                <div class="player-name">${hand.llm1_name}</div>
                <div class="player-cards">${formatCards(hand.llm1_hole_cards)}</div>
                <div class="player-result ${getPerformanceClass(hand.llm1_winnings)}">${formatNumber(hand.llm1_winnings)}</div>
            </div>
            
            <div class="vs-indicator">VS</div>
            
            <div class="player-info ${winner === 'llm2' ? 'winner' : winner === 'llm1' ? 'loser' : ''}">
                <div class="player-name">${hand.llm2_name}</div>
                <div class="player-cards">${formatCards(hand.llm2_hole_cards)}</div>
                <div class="player-result ${getPerformanceClass(hand.llm2_winnings)}">${formatNumber(hand.llm2_winnings)}</div>
            </div>
        </div>
        
        ${hand.community_cards ? `
            <div class="community-cards">
                <div class="cards">${formatCards(hand.community_cards)}</div>
            </div>
        ` : ''}
        
        <div class="hand-details">
            <div class="detail-item">
                <div class="detail-value">${hand.pot_size}</div>
                <div class="detail-label">Pot Size</div>
            </div>
            <div class="detail-item">
                <div class="detail-value">${hand.showdown ? 'Yes' : 'No'}</div>
                <div class="detail-label">Showdown</div>
            </div>
            <div class="detail-item">
                <div class="detail-value">${totalActions}</div>
                <div class="detail-label">Actions</div>
            </div>
            <div class="detail-item">
                <div class="detail-value ${fallbackCount > 0 ? 'fallback-high' : 'fallback-low'}">${fallbackCount}</div>
                <div class="detail-label">Fallbacks</div>
            </div>
        </div>
    `;
    
    return card;
}

function formatCards(cardsJson) {
    try {
        const cards = JSON.parse(cardsJson);
        if (!Array.isArray(cards) || cards.length === 0) {
            return '-- --';
        }
        return cards.join(' ');
    } catch (e) {
        return '-- --';
    }
}

function showHandDetails(hand) {
    const modal = document.getElementById('hand-modal');
    const modalTitle = document.getElementById('modal-title');
    const handDetails = document.getElementById('hand-details');
    
    modalTitle.textContent = `Hand #${hand.hand_number}: ${hand.llm1_name} vs ${hand.llm2_name}`;
    
    // Parse actions
    let actions = [];
    try {
        actions = JSON.parse(hand.actions);
    } catch (e) {
        actions = [];
    }
    
    handDetails.innerHTML = `
        <div class="hand-detail-grid">
            <div class="detail-section">
                <h4>${hand.llm1_name}</h4>
                <p><strong>Hole Cards:</strong> ${formatCards(hand.llm1_hole_cards)}</p>
                <p><strong>Hand Strength:</strong> ${hand.hand_strength_llm1 || 'Unknown'}</p>
                <p><strong>Winnings:</strong> <span class="${getPerformanceClass(hand.llm1_winnings)}">${formatNumber(hand.llm1_winnings)}</span></p>
            </div>
            
            <div class="detail-section">
                <h4>${hand.llm2_name}</h4>
                <p><strong>Hole Cards:</strong> ${formatCards(hand.llm2_hole_cards)}</p>
                <p><strong>Hand Strength:</strong> ${hand.hand_strength_llm2 || 'Unknown'}</p>
                <p><strong>Winnings:</strong> <span class="${getPerformanceClass(hand.llm2_winnings)}">${formatNumber(hand.llm2_winnings)}</span></p>
            </div>
            
            <div class="detail-section">
                <h4>Hand Info</h4>
                <p><strong>Community Cards:</strong> ${formatCards(hand.community_cards)}</p>
                <p><strong>Final Pot:</strong> ${hand.pot_size} chips</p>
                <p><strong>Winner:</strong> ${getWinnerName(hand)}</p>
                <p><strong>Showdown:</strong> ${hand.showdown ? 'Yes' : 'No'}</p>
            </div>
        </div>
        
        <div class="action-timeline">
            <h4>Action Timeline</h4>
            ${createActionTimeline(actions)}
        </div>
    `;
    
    modal.style.display = 'block';
}

function createActionTimeline(actions) {
    if (!actions || actions.length === 0) {
        return '<p>No actions recorded for this hand.</p>';
    }
    
    return actions.map(action => `
        <div class="timeline-item ${action.is_fallback ? 'fallback' : ''}">
            <div class="timeline-player">${action.player}</div>
            <div class="timeline-action">
                ${action.action}${action.amount > 0 ? ` ${action.amount}` : ''}
                ${action.is_fallback ? ' <i class="fas fa-exclamation-triangle" title="Fallback action"></i>' : ''}
            </div>
            <div class="timeline-result">
                Stack: ${action.stack_after} | Pot: ${action.pot_after}
            </div>
        </div>
    `).join('');
}

function getWinnerName(hand) {
    switch (hand.winner) {
        case 'llm1': return hand.llm1_name;
        case 'llm2': return hand.llm2_name;
        case 'split': return 'Split Pot';
        default: return 'Unknown';
    }
}

function updatePagination() {
    const totalPages = Math.ceil(filteredHands.length / handsPerPage);
    
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
}

function updateStats() {
    const totalHands = filteredHands.length;
    const showdownHands = filteredHands.filter(hand => hand.showdown).length;
    const totalPot = filteredHands.reduce((sum, hand) => sum + hand.pot_size, 0);
    const avgPot = totalHands > 0 ? (totalPot / totalHands).toFixed(0) : 0;
    
    // Calculate fallback rate
    let totalActions = 0;
    let totalFallbacks = 0;
    
    filteredHands.forEach(hand => {
        try {
            const actions = JSON.parse(hand.actions);
            totalActions += actions.length;
            totalFallbacks += actions.filter(action => action.is_fallback).length;
        } catch (e) {
            // Skip if actions can't be parsed
        }
    });
    
    const fallbackRate = totalActions > 0 ? ((totalFallbacks / totalActions) * 100).toFixed(1) : 0;
    
    document.getElementById('total-hands').textContent = totalHands.toLocaleString();
    document.getElementById('showdown-hands').textContent = showdownHands.toLocaleString();
    document.getElementById('avg-pot').textContent = avgPot;
    document.getElementById('fallback-rate').textContent = fallbackRate + '%';
}

function setLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement && window.benchmarkData?.lastUpdated) {
        lastUpdatedElement.textContent = formatDate(window.benchmarkData.lastUpdated);
    }
}

function showError(message) {
    const container = document.getElementById('hands-container');
    if (container) {
        container.innerHTML = `
            <div class="error">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Error:</strong> ${message}
            </div>
        `;
    }
}
