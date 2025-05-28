document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const playerNameInput = document.getElementById('playerNameInput');
    const seasonSelect = document.getElementById('seasonSelect');
    const searchButton = document.getElementById('searchButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorDisplay = document.getElementById('errorDisplay');
    const resultsArea = document.getElementById('resultsArea');
    const initialMessage = document.getElementById('initialMessage');

    // Results display elements
    const playerNameDisplay = document.getElementById('playerNameDisplay');
    const individualStatsChartCanvas = document.getElementById('individualStatsChart');
    const weaponStatsDisplay = document.getElementById('weaponStatsDisplay');
    const teammatesDisplay = document.getElementById('teammatesDisplay');
    const matchLogsDisplay = document.getElementById('matchLogsDisplay');

    let individualStatsChartInstance = null; // To hold the chart instance for updates
    const teammateChartInstances = {}; // To hold teammate chart instances

    // --- Chart.js Global Config (Optional) ---
    Chart.defaults.color = 'rgba(234, 234, 234, 0.8)'; // Light text for chart labels/ticks
    Chart.defaults.borderColor = 'rgba(255, 204, 0, 0.3)'; // Accent color for lines/borders

    // --- Initialization ---
    fetchSeasons();

    // --- Event Listeners ---
    if (searchButton) {
        searchButton.addEventListener('click', handleSearch);
    }

    // --- Core Functions ---
    async function fetchSeasons() {
        try {
            const response = await fetch('/api/seasons'); // Backend endpoint to be created
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Failed to fetch seasons, server returned an error.' }));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const seasonsData = await response.json();
            
            seasonSelect.innerHTML = '<option value="">Select a Season</option>'; // Clear loading/default
            if (seasonsData && seasonsData.data) {
                seasonsData.data.forEach(season => {
                    const option = document.createElement('option');
                    option.value = season.id;
                    // Use a more descriptive name if available, otherwise fallback to ID
                    option.textContent = season.attributes?.isCurrentSeason ? `${season.id} (Current)` : season.id;
                    if (season.attributes?.isCurrentSeason) {
                        option.selected = true; // Auto-select current season
                    }
                    seasonSelect.appendChild(option);
                });
            } else {
                 seasonSelect.innerHTML = '<option value="">No seasons available</option>';
                 console.warn("Seasons data received but not in expected format:", seasonsData);
            }
        } catch (error) {
            console.error("Failed to fetch seasons:", error);
            seasonSelect.innerHTML = '<option value="">Error loading seasons</option>';
            showError(`Error loading seasons: ${error.message}`);
        }
    }

    async function handleSearch() {
        const playerName = playerNameInput.value.trim();
        const seasonId = seasonSelect.value;

        if (!playerName) {
            showError("Please enter a player name.");
            return;
        }
        if (!seasonId) {
            showError("Please select a season.");
            return;
        }

        console.log(`Searching for player: ${playerName}, season: ${seasonId}`);
        showLoading(true);
        hideError();
        resultsArea.style.display = 'none'; // Hide previous results
        initialMessage.style.display = 'none';


        try {
            // TODO: The backend for this endpoint will be created in Step 6.
            // This fetch will likely fail until then, or return placeholder data if you set one up.
            const response = await fetch(`/api/player_stats?playerName=${encodeURIComponent(playerName)}&seasonId=${encodeURIComponent(seasonId)}`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: 'Server returned an error. Please check console for details.' }));
                throw new Error(errorData.error || errorData.message || `HTTP error! status: ${response.status}`);
            }
            const stats = await response.json();
            console.log("Received player stats:", stats);

            if (stats.error) { // Handle application-level errors from backend
                throw new Error(stats.error);
            }
            
            renderAllStats(stats, playerName);
            resultsArea.style.display = 'block'; // Show results

        } catch (error) {
            console.error("Failed to fetch player stats:", error);
            showError(`Failed to load player stats: ${error.message}`);
            clearAllStatsDisplay(); // Clear any stale data
        } finally {
            showLoading(false);
        }
    }

    // --- Rendering Functions ---
    function renderAllStats(data, playerName) {
        playerNameDisplay.textContent = data.playerName || playerName; // Use name from data if available

        // 1. Individual Stats Chart
        if (data.individualStats) {
            const { damageDealt, kills, assists, survivalTime, avgRank } = data.individualStats;
             // For radar chart, higher "avgRank" (closer to 1) is better. Our current calculation (0-100) needs to be normalized or interpreted.
             // If avgRank is a score 0-100 (higher better), it's fine.
             // If it's actual rank (1 is best), we need to invert or scale it for the chart.
             // Assuming current avgRank is a score where higher is better for the chart.
            createOrUpdateRadarChart(
                individualStatsChartCanvas,
                'individualStatsChartInstance', // key to store the chart instance
                'Overall Performance',
                ['Damage/Match', 'Kills/Match', 'Assists/Match', 'Avg Survival (s)', 'Rank Score (0-100)'],
                [damageDealt, kills, assists, survivalTime, avgRank]
            );
        } else {
            console.warn("Individual stats missing from response.");
            if (individualStatsChartInstance) individualStatsChartInstance.destroy();
            individualStatsChartCanvas.getContext('2d').clearRect(0, 0, individualStatsChartCanvas.width, individualStatsChartCanvas.height); // Clear canvas
        }

        // 2. Weapon Stats (Placeholder for now as per task)
        weaponStatsDisplay.innerHTML = ''; // Clear previous
        if (data.weaponStats && Object.keys(data.weaponStats).length > 0) {
            const list = document.createElement('ul');
            for (const category in data.weaponStats) {
                const item = document.createElement('li');
                const ws = data.weaponStats[category];
                item.textContent = `${category}: ${ws.topWeapon || 'N/A'} (Dmg/Match: ${ws.damagePerMatch || 0}) - ${ws.info || ''}`;
                list.appendChild(item);
            }
            weaponStatsDisplay.appendChild(list);
        } else {
            weaponStatsDisplay.innerHTML = '<p>Weapon stats data not available or placeholder as per current implementation.</p>';
        }
        
        // 3. Teammate Synergy
        teammatesDisplay.innerHTML = ''; // Clear previous
        if (data.frequentTeammates && data.frequentTeammates.length > 0) {
            data.frequentTeammates.forEach((teammate, index) => {
                const teammateCard = document.createElement('div');
                teammateCard.className = 'teammate-synergy-card'; // For styling

                const nameHeader = document.createElement('h4');
                nameHeader.textContent = `${teammate.playerName} (${teammate.matchesTogether} matches together)`;
                teammateCard.appendChild(nameHeader);

                if (teammate.synergyStats) {
                    const canvasId = `teammateChart_${teammate.accountId || index}`; // Ensure unique ID
                    const canvas = document.createElement('canvas');
                    canvas.id = canvasId;
                    teammateCard.appendChild(canvas);
                    
                    const { damageDealt, kills, assists, survivalTime, avgRank } = teammate.synergyStats;
                    // For avgRank in synergy: lower is better (team rank). For chart, we might want to invert or show as is.
                    // Let's assume for radar chart, higher values are "better".
                    // If avgRank is actual rank (1=best), we might need to scale it or present it differently.
                    // For this placeholder, let's use it as is, but note it for interpretation.
                    // Or, create a "Team Performance Score" from rank (e.g., 100 - avgRank)
                    const teamPerformanceScore = 100 - avgRank; // Example: if avgRank is 5, score is 95. Max possible rank could be 100.
                                                              // This needs careful thought based on typical rank range.
                                                              // Let's use a simpler direct display for now and refine later.

                    createOrUpdateRadarChart(
                        canvas,
                        `teammateChart_${teammate.accountId || index}`, // key for instance storage
                        `Synergy with ${teammate.playerName}`,
                        ['Avg Dmg/Match', 'Avg Kills/Match', 'Avg Assists/Match', 'Avg Survival (s)', 'Avg Team Rank'],
                        [damageDealt, kills, assists, survivalTime, avgRank] // Lower avgRank is better.
                    );
                } else {
                    const noStats = document.createElement('p');
                    noStats.textContent = 'Synergy stats not available for this teammate.';
                    teammateCard.appendChild(noStats);
                }
                teammatesDisplay.appendChild(teammateCard);
            });
        } else {
            teammatesDisplay.innerHTML = '<p>No frequent teammate data to display for this season, or data not available.</p>';
        }

        // 4. Match Logs
        matchLogsDisplay.innerHTML = ''; // Clear previous
        if (data.matchLogs && data.matchLogs.length > 0) {
            const list = document.createElement('ul');
            data.matchLogs.forEach(match => {
                const item = document.createElement('li');
                // Example: "Match ID: xyz123 - Mode: squad-fpp - Kills: 5, Damage: 300"
                // This depends on what backend provides for match logs
                item.textContent = `Match ID: ${match.id} - Rank: ${match.rank || 'N/A'}, Kills: ${match.kills || 0}, Damage: ${match.damageDealt || 0} (${match.gameMode || 'N/A'})`;
                list.appendChild(item);
            });
            matchLogsDisplay.appendChild(list);
        } else {
            matchLogsDisplay.innerHTML = '<p>No recent match logs to display for this season, or data not available.</p>';
        }
    }

    function createOrUpdateRadarChart(canvasElement, chartInstanceKey, chartLabel, dataLabels, dataValues) {
        if (!canvasElement) {
            console.error("Canvas element not provided for chart:", chartInstanceKey);
            return;
        }
        const ctx = canvasElement.getContext('2d');
        if (!ctx) {
            console.error("Could not get 2D context for canvas:", chartInstanceKey);
            return;
        }

        // Normalize data for radar chart (0-100 scale is often good)
        // This is a placeholder normalization - specific logic depends on expected data ranges.
        // For now, we assume values are somewhat comparable or Chart.js will scale them.
        // A more robust solution would involve knowing max possible values for each stat.
        const normalizedValues = dataValues.map(val => Math.max(0, val)); // Ensure no negative values for radar

        const data = {
            labels: dataLabels,
            datasets: [{
                label: chartLabel,
                data: normalizedValues,
                fill: true,
                backgroundColor: 'rgba(249, 181, 0, 0.2)', // PUBG Yellow, semi-transparent
                borderColor: 'rgb(249, 181, 0)',
                pointBackgroundColor: 'rgb(249, 181, 0)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(249, 181, 0)'
            }]
        };

        const config = {
            type: 'radar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allow chart to fill container
                elements: {
                    line: {
                        borderWidth: 2
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(234, 234, 234, 0.4)' // Lighter lines for readability
                        },
                        grid: {
                            color: 'rgba(234, 234, 234, 0.4)'
                        },
                        pointLabels: {
                            color: 'rgba(234, 234, 234, 0.85)', // Text for labels like "Kills", "Damage"
                            font: {
                                size: 11 // Adjust as needed
                            }
                        },
                        ticks: {
                            color: 'rgba(234, 234, 234, 0.8)', // Numbers on the scale
                            backdropColor: 'rgba(0,0,0,0.5)', // Background for ticks for readability
                            font: {
                                size: 10
                            },
                            // SuggestedMin and suggestedMax can help scale, but dynamic data is tricky.
                            // Chart.js usually does a good job auto-scaling.
                            // Forcing a 0-100 scale might be an option if all data is normalized.
                            // For now, let Chart.js auto-scale.
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                             color: 'rgba(234, 234, 234, 0.9)'
                        }
                    }
                }
            }
        };

        // Store chart instances to destroy them before re-rendering
        if (chartInstanceKey === 'individualStatsChartInstance') {
            if (individualStatsChartInstance) {
                individualStatsChartInstance.destroy();
            }
            individualStatsChartInstance = new Chart(ctx, config);
        } else {
            if (teammateChartInstances[chartInstanceKey]) {
                teammateChartInstances[chartInstanceKey].destroy();
            }
            teammateChartInstances[chartInstanceKey] = new Chart(ctx, config);
        }
    }
    
    function clearAllStatsDisplay() {
        playerNameDisplay.textContent = 'Player Name';
        if (individualStatsChartInstance) {
            individualStatsChartInstance.destroy();
            individualStatsChartInstance = null;
        }
        // Clear teammate charts
        Object.keys(teammateChartInstances).forEach(key => {
            if (teammateChartInstances[key]) {
                teammateChartInstances[key].destroy();
            }
        });
        for (const key in teammateChartInstances) delete teammateChartInstances[key];


        const canvasCtx = individualStatsChartCanvas.getContext('2d');
        if (canvasCtx) canvasCtx.clearRect(0, 0, individualStatsChartCanvas.width, individualStatsChartCanvas.height);
        
        weaponStatsDisplay.innerHTML = '<p>Weapon statistics will be displayed here.</p>';
        teammatesDisplay.innerHTML = '<p>Frequent teammate data will appear here.</p>';
        matchLogsDisplay.innerHTML = '<p>Recent match logs will appear here.</p>';
        resultsArea.style.display = 'none';
        initialMessage.style.display = 'block';
    }


    // --- UI Helper Functions ---
    function showLoading(isLoading) {
        if (loadingIndicator) {
            loadingIndicator.style.display = isLoading ? 'block' : 'none';
        }
    }

    function showError(message) {
        if (errorDisplay) {
            errorDisplay.textContent = message;
            errorDisplay.style.display = 'block';
        }
    }

    function hideError() {
        if (errorDisplay) {
            errorDisplay.style.display = 'none';
        }
    }

});
