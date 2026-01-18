// Cost vs Performance visualization
// Fetches pricing from OpenRouter and plots against benchmark performance

let costPerformanceChart = null;

function getOpenRouterModelId(llm) {
    // Check if model field already contains the full OpenRouter ID (e.g., "google/gemini-3-flash-preview")
    const model = llm.model && llm.model.trim();
    if (model && model.includes('/')) {
        // Model field already contains the full OpenRouter model ID
        return model;
    }
    
    // Otherwise, construct from provider/model
    const provider = llm.provider && llm.provider.trim();
    if (provider && model) {
        // Construct the OpenRouter model ID
        return `${provider.toLowerCase()}/${model}`;
    }
    
    return null;
}

function findOpenRouterModel(pricingData, targetId) {
    // Try exact match first
    let model = pricingData.find(m => m.id === targetId);
    if (model) return model;
    
    // Try case-insensitive match
    model = pricingData.find(m => m.id && m.id.toLowerCase() === targetId.toLowerCase());
    if (model) return model;
    
    // Try matching just the model name (without provider)
    const modelName = targetId.split('/').pop();
    model = pricingData.find(m => {
        if (!m.id) return false;
        const mModelName = m.id.split('/').pop();
        return mModelName.toLowerCase() === modelName.toLowerCase();
    });
    if (model) return model;
    
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    
    // Add event listeners for metric changes
    document.getElementById('cost-metric-select').addEventListener('change', updateChart);
    document.getElementById('performance-metric-select').addEventListener('change', updateChart);
    
    setLastUpdated();
});

function initializePage() {
    const loadingDiv = document.getElementById('chart-loading');
    const errorDiv = document.getElementById('chart-error');
    
    // Hide error initially
    errorDiv.style.display = 'none';
    
    // Fetch pricing data from OpenRouter
    fetchOpenRouterPricing()
        .then(pricingData => {
            loadingDiv.style.display = 'none';
            createChart(pricingData);
        })
        .catch(error => {
            console.error('Error fetching pricing:', error);
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            document.getElementById('error-message').textContent = 
                'Failed to load pricing data from OpenRouter. ' + error.message;
        });
}

async function fetchOpenRouterPricing() {
    try {
        const response = await fetch('https://openrouter.ai/api/v1/models', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.data || [];
    } catch (error) {
        throw new Error(`Failed to fetch OpenRouter pricing: ${error.message}`);
    }
}

function createChart(pricingData) {
    const benchmarkData = window.benchmarkData;
    if (!benchmarkData || !benchmarkData.leaderboard) {
        throw new Error('Benchmark data not available');
    }
    
    // Debug: Log what we have
    console.log(`Processing ${benchmarkData.leaderboard.length} models from benchmark data`);
    console.log(`Received ${pricingData.length} models from OpenRouter`);
    
    // Build pricing lookup map (exact match)
    const pricingMap = {};
    pricingData.forEach(model => {
        if (model.id) {
            pricingMap[model.id] = {
                input: model.pricing?.prompt || 0,
                output: model.pricing?.completion || 0,
                average: ((model.pricing?.prompt || 0) + (model.pricing?.completion || 0)) / 2
            };
        }
    });
    
    // Debug: Show sample OpenRouter model IDs
    const sampleModelIds = Object.keys(pricingMap).slice(0, 5);
    console.log('Sample OpenRouter model IDs:', sampleModelIds);
    
    // Prepare chart data
    const chartData = [];
    const labels = [];
    const unmatchedModels = [];
    
    benchmarkData.leaderboard.forEach(llm => {
        // Debug: Log model info
        if (!llm.provider || !llm.model || !llm.provider.trim() || !llm.model.trim()) {
            console.warn(`Model ${llm.name} missing provider/model info:`, {
                provider: llm.provider || '(empty)',
                model: llm.model || '(empty)'
            });
        }
        
        const openRouterId = getOpenRouterModelId(llm);
        if (!openRouterId) {
            console.warn(`No OpenRouter mapping found for model: ${llm.name} (provider: ${llm.provider || 'missing'}, model: ${llm.model || 'missing'})`);
            unmatchedModels.push({ name: llm.name, reason: 'No provider/model info', provider: llm.provider, model: llm.model });
            return;
        }
        
        console.log(`Looking for pricing for: ${llm.name} -> ${openRouterId}`);
        
        // Try to find pricing - first exact match, then flexible match
        let pricing = pricingMap[openRouterId];
        let matchedId = openRouterId;
        
        if (!pricing) {
            // Try flexible matching
            const matchedModel = findOpenRouterModel(pricingData, openRouterId);
            if (matchedModel) {
                matchedId = matchedModel.id;
                pricing = {
                    input: matchedModel.pricing?.prompt || 0,
                    output: matchedModel.pricing?.completion || 0,
                    average: ((matchedModel.pricing?.prompt || 0) + (matchedModel.pricing?.completion || 0)) / 2
                };
                console.log(`Matched ${llm.name} (${openRouterId}) to OpenRouter model: ${matchedId}`);
            }
        }
        
        if (!pricing) {
            console.warn(`No pricing data found for model: ${openRouterId} (tried: ${openRouterId})`);
            unmatchedModels.push({ name: llm.name, tried: openRouterId });
            return;
        }
        
        const costMetric = document.getElementById('cost-metric-select').value;
        const performanceMetric = document.getElementById('performance-metric-select').value;
        
        // OpenRouter pricing is per 1M tokens, so we need to convert if needed
        // Pricing might be in different formats, handle both cases
        let cost = pricing[costMetric] || pricing.average || 0;
        
        // If cost is very small (like 0.00001), it might already be per token
        // OpenRouter typically provides pricing per 1M tokens, so values like 0.01 mean $0.01 per 1M tokens
        // But if we see values like 0.00001, they might be per token and need to be multiplied
        // For now, assume OpenRouter provides per 1M tokens directly
        if (cost > 0 && cost < 0.0001) {
            // This looks like per-token pricing, multiply by 1M
            cost = cost * 1000000;
        }
        
        const performance = llm[performanceMetric] || 0;
        
        if (cost > 0 && performance !== undefined) {
            chartData.push({
                x: cost,
                y: performance,
                label: llm.name,
                rank: llm.rank,
                avgPerHand: llm.avgPerHand,
                winRate: llm.winRate
            });
            labels.push(llm.name);
        }
    });
    
    if (chartData.length === 0) {
        // Provide helpful error message with debugging info
        const errorMsg = unmatchedModels.length > 0 
            ? `No data points available. Unmatched models: ${unmatchedModels.map(m => m.name).join(', ')}. ` +
              `Make sure models are registered with correct provider/model info.`
            : 'No data points available after matching models with pricing. ' +
              `Found ${benchmarkData.leaderboard.length} models in leaderboard, ` +
              `${pricingData.length} models from OpenRouter.`;
        throw new Error(errorMsg);
    }
    
    // Log summary
    console.log(`Successfully matched ${chartData.length} models with pricing data`);
    if (unmatchedModels.length > 0) {
        console.warn(`Could not match ${unmatchedModels.length} models:`, unmatchedModels);
    }
    
    // Get canvas context
    const ctx = document.getElementById('costPerformanceChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (costPerformanceChart) {
        costPerformanceChart.destroy();
    }
    
    // Create scatter plot
    costPerformanceChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'LLM Performance vs Cost',
                data: chartData,
                backgroundColor: function(context) {
                    const point = context.parsed;
                    const avgPerHand = chartData[context.dataIndex]?.avgPerHand || 0;
                    // Color based on performance: green for positive, red for negative
                    return avgPerHand >= 0 ? 'rgba(75, 192, 192, 0.6)' : 'rgba(255, 99, 132, 0.6)';
                },
                borderColor: function(context) {
                    const avgPerHand = chartData[context.dataIndex]?.avgPerHand || 0;
                    return avgPerHand >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)';
                },
                borderWidth: 2,
                pointRadius: 8,
                pointHoverRadius: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.5,
            plugins: {
                title: {
                    display: true,
                    text: 'LLM Performance vs API Cost',
                    font: {
                        size: 18
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return context[0].raw.label || '';
                        },
                        label: function(context) {
                            const point = chartData[context.dataIndex];
                            const costMetric = document.getElementById('cost-metric-select').value;
                            const performanceMetric = document.getElementById('performance-metric-select').value;
                            
                            let costLabel = 'Cost';
                            if (costMetric === 'input') costLabel = 'Input Cost';
                            else if (costMetric === 'output') costLabel = 'Output Cost';
                            else if (costMetric === 'average') costLabel = 'Avg Cost';
                            
                            let perfLabel = 'Performance';
                            if (performanceMetric === 'avgPerHand') perfLabel = 'Avg Chips/Hand';
                            else if (performanceMetric === 'winRate') perfLabel = 'Win Rate (%)';
                            
                            return [
                                `${costLabel}: $${context.parsed.x.toFixed(2)} per 1M tokens`,
                                `${perfLabel}: ${context.parsed.y.toFixed(2)}`,
                                `Rank: #${point.rank}`,
                                `Total Hands: ${point.avgPerHand !== undefined ? benchmarkData.leaderboard.find(l => l.name === point.label)?.totalHands || 'N/A' : 'N/A'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: (() => {
                            const costMetric = document.getElementById('cost-metric-select').value;
                            if (costMetric === 'input') return 'Input Cost ($ per 1M tokens)';
                            if (costMetric === 'output') return 'Output Cost ($ per 1M tokens)';
                            return 'Average Cost ($ per 1M tokens)';
                        })(),
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    type: 'linear',
                    position: 'bottom',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            // Format as currency, avoiding scientific notation
                            // OpenRouter pricing is per 1M tokens
                            if (value === 0 || value === null || value === undefined) return '$0';
                            
                            // Ensure value is a number
                            const numValue = typeof value === 'number' ? value : parseFloat(value);
                            
                            if (isNaN(numValue) || numValue === 0) return '$0';
                            
                            // Format based on magnitude - toFixed prevents scientific notation
                            if (numValue < 0.0001) {
                                // Very small values - show with more precision
                                return '$' + numValue.toFixed(6);
                            } else if (numValue < 0.01) {
                                return '$' + numValue.toFixed(4);
                            } else if (numValue < 1) {
                                return '$' + numValue.toFixed(2);
                            } else {
                                return '$' + numValue.toFixed(2);
                            }
                        },
                        maxRotation: 0,
                        minRotation: 0
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: (() => {
                            const performanceMetric = document.getElementById('performance-metric-select').value;
                            if (performanceMetric === 'avgPerHand') return 'Average Chips per Hand';
                            if (performanceMetric === 'winRate') return 'Win Rate (%)';
                            return 'Performance';
                        })(),
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    beginAtZero: false
                }
            },
            interaction: {
                intersect: false,
                mode: 'point'
            }
        }
    });
}

function updateChart() {
    // If chart already exists, update it with new data
    if (costPerformanceChart) {
        const loadingDiv = document.getElementById('chart-loading');
        const errorDiv = document.getElementById('chart-error');
        
        errorDiv.style.display = 'none';
        loadingDiv.style.display = 'block';
        
        fetchOpenRouterPricing()
            .then(pricingData => {
                loadingDiv.style.display = 'none';
                createChart(pricingData);
            })
            .catch(error => {
                console.error('Error updating chart:', error);
                loadingDiv.style.display = 'none';
                errorDiv.style.display = 'block';
                document.getElementById('error-message').textContent = 
                    'Failed to update chart: ' + error.message;
            });
    } else {
        // Chart doesn't exist yet, initialize it
        initializePage();
    }
}

function setLastUpdated() {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement && window.benchmarkData && window.benchmarkData.lastUpdated) {
        lastUpdatedElement.textContent = formatDate(window.benchmarkData.lastUpdated);
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        return dateString;
    }
}
