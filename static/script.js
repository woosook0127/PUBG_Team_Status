document.addEventListener('DOMContentLoaded', () => {
    const getStatsBtn = document.getElementById('getStatsBtn');
    const playerNameInput = document.getElementById('playerName');
    const platformSelect = document.getElementById('platform');
    const seasonIdInput = document.getElementById('seasonId');
    const statsOutput = document.getElementById('statsOutput');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorDisplay = document.getElementById('errorDisplay');

    // Team Performance Elements
    const teamPerformanceSection = document.getElementById('teamPerformanceSection');
    const teamIdentificationMessage = document.getElementById('teamIdentificationMessage');
    const teamChartsContainer = document.getElementById('teamChartsContainer');
    const teamErrorDisplay = document.getElementById('teamErrorDisplay');
    
    // Overall Team Stats Elements
    const overallTeamStatsSection = document.getElementById('overallTeamStatsSection'); // Ensure this is used to show/hide section
    const overallTeamStatsMessage = document.getElementById('overallTeamStatsMessage');
    const overallTeamStatsOutput = document.getElementById('overallTeamStatsOutput');
    const overallTeamErrorDisplay = document.getElementById('overallTeamErrorDisplay');

    let currentCharts = []; 

    getStatsBtn.addEventListener('click', async () => {
        const playerName = playerNameInput.value.trim();
        const platform = platformSelect.value;
        const seasonId = seasonIdInput.value.trim();

        // Client-side validation
        if (!playerName) {
            displayError("Player Name is required. Please enter a player name.", errorDisplay);
            return;
        }
        if (playerName.length < 2 || playerName.length > 20) { // Example length check
            displayError("Player Name must be between 2 and 20 characters.", errorDisplay);
            return;
        }
        if (!/^[a-zA-Z0-9_.-]*$/.test(playerName)) { // Example character check
            displayError("Player Name contains invalid characters. Use letters, numbers, underscores, hyphens, or periods.", errorDisplay);
            return;
        }

        if (!seasonId) {
            displayError("Season ID is required. Please enter a season ID.", errorDisplay);
            return;
        }
        // Example: Basic season ID format check (very generic, PUBG season IDs are complex)
        if (!/^division\.bro\.official\.[a-z0-9-]+$/.test(seasonId) && !/pc-[0-9]{4}-[0-9]{2}/.test(seasonId) && !/xbox-[0-9]{4}-[0-9]{2}/.test(seasonId) && !/psn-[0-9]{4}-[0-9]{2}/.test(seasonId) && !/kakao-[0-9]{4}-[0-9]{2}/.test(seasonId)) {
            // This regex is highly simplified and likely won't cover all valid season ID formats.
            // It's just an example of adding some client-side format hint.
            // displayError("Season ID format seems incorrect. Example: 'division.bro.official.steam-2023-07'", errorDisplay);
            // return; // Commenting out for now as season IDs are too varied.
        }


        clearAllResults();
        loadingIndicator.style.display = 'block'; // Show main loading indicator

        let individualStatsFailed = false;

        try {
            // --- 1. Fetch Individual Weapon Stats ---
            const individualStatsResponse = await fetch(`/players/${platform}/${playerName}/seasons/${seasonId}/individual-weapon-stats`);
            if (!individualStatsResponse.ok) {
                individualStatsFailed = true;
                const errorData = await individualStatsResponse.json().catch(() => ({ detail: "Error fetching individual stats. Response not JSON." }));
                handleFetchError(errorData, individualStatsResponse, errorDisplay, playerName, platform, seasonId, "Individual Weapon Stats");
            } else {
                const individualStatsData = await individualStatsResponse.json();
                displayIndividualStats(individualStatsData);
            }

            // --- 2. Fetch Team Performance Comparison (Radar Charts) ---
            if (!individualStatsFailed) { // Only proceed if individual stats didn't critically fail (e.g. player not found)
                teamPerformanceSection.style.display = 'block'; 
                const teamPerformanceResponse = await fetch(`/players/${platform}/${playerName}/seasons/${seasonId}/team-performance-comparison`);
                if (!teamPerformanceResponse.ok) {
                    const errorData = await teamPerformanceResponse.json().catch(() => ({ detail: "Error fetching team performance. Response not JSON." }));
                    handleFetchError(errorData, teamPerformanceResponse, teamErrorDisplay, playerName, platform, seasonId, "Team Performance Comparison");
                } else {
                    const teamPerformanceData = await teamPerformanceResponse.json();
                    displayTeamPerformance(teamPerformanceData);
                }
            } else {
                 displayError("Skipping team stats as initial player/season data failed to load.", teamErrorDisplay);
            }


            // --- 3. Fetch Overall Team Stats ---
            if (!individualStatsFailed) { // Similar condition
                overallTeamStatsSection.style.display = 'block'; 
                const overallStatsResponse = await fetch(`/players/${platform}/${playerName}/seasons/${seasonId}/overall-team-stats`);
                if (!overallStatsResponse.ok) {
                    const errorData = await overallStatsResponse.json().catch(() => ({ detail: "Error fetching overall team stats. Response not JSON." }));
                    handleFetchError(errorData, overallStatsResponse, overallTeamErrorDisplay, playerName, platform, seasonId, "Overall Team Stats");
                } else {
                    const overallStatsData = await overallStatsResponse.json();
                    displayOverallTeamStats(overallStatsData);
                }
            } else {
                displayError("Skipping overall team stats as initial player/season data failed to load.", overallTeamErrorDisplay);
            }

        } catch (error) { // General network or unexpected JS error
            console.error("Fetch error in main sequence:", error);
            displayError(`A critical error occurred: ${error.message}. Check the console.`, errorDisplay);
            if (teamPerformanceSection.style.display === 'block') {
                displayError("Team performance could not be loaded due to a critical error.", teamErrorDisplay);
            }
            if (overallTeamStatsSection.style.display === 'block') {
                 displayError("Overall team stats could not be loaded due to a critical error.", overallTeamErrorDisplay);
            }
        } finally {
            loadingIndicator.style.display = 'none'; 
        }
    });

    function handleFetchError(errorData, response, errorElement, playerName, platform, seasonId, sectionName = "Stats") {
        // Use the detail from JSON response if available, otherwise default to statusText
        let detailMessage = errorData.detail || response.statusText || "Unknown error";
        
        // If the detail message from backend is already user-friendly (due to custom exceptions), use it.
        // Otherwise, craft a more user-friendly one here.
        let userFriendlyMessage = "";

        switch (response.status) {
            case 400:
                userFriendlyMessage = `Bad Request for ${sectionName}: ${detailMessage}. Please check your input.`;
                break;
            case 401:
            case 403:
                userFriendlyMessage = `Access Denied for ${sectionName}: ${detailMessage}. API key might be invalid or lacking permissions.`;
                break;
            case 404:
                if (detailMessage.toLowerCase().includes("player") && detailMessage.toLowerCase().includes("not found")) {
                    userFriendlyMessage = `Player '${playerName}' not found on platform '${platform}'. Please verify the name and platform.`;
                } else if (detailMessage.toLowerCase().includes("season") && detailMessage.toLowerCase().includes("not found")) {
                    userFriendlyMessage = `Season '${seasonId}' not found for player '${playerName}' on platform '${platform}'.`;
                } else if (detailMessage.toLowerCase().includes("clan") && detailMessage.toLowerCase().includes("not found")) {
                     userFriendlyMessage = `Clan information not found for player '${playerName}'. The player may not be in a clan.`;
                } else if (detailMessage.toLowerCase().includes("match") && detailMessage.toLowerCase().includes("not found")) {
                    userFriendlyMessage = `A specific match required for ${sectionName} was not found. Data might be incomplete.`;
                }
                else {
                    userFriendlyMessage = `${sectionName} not found: ${detailMessage}.`;
                }
                break;
            case 429:
                userFriendlyMessage = `Too many requests for ${sectionName}: ${detailMessage}. Please wait a moment and try again.`;
                break;
            case 500:
            case 503:
                userFriendlyMessage = `Server Error for ${sectionName}: ${detailMessage}. The service might be temporarily unavailable. Please try again later.`;
                break;
            default:
                userFriendlyMessage = `Error fetching ${sectionName} (${response.status}): ${detailMessage}.`;
        }
        
        displayError(userFriendlyMessage, errorElement);
    }

    function displayIndividualStats(data) {
        statsOutput.innerHTML = ''; 
        const header = document.createElement('div');
        header.innerHTML = `
            <h3>Weapon Stats for ${escapeHtml(data.player_name)} (${escapeHtml(data.platform)}) - Season ${escapeHtml(data.season_id)}</h3>
            <p><strong>Total Matches Played in Season (for weapon stats):</strong> ${data.total_matches_played}</p>
            <hr>
        `;
        statsOutput.appendChild(header);

        if (Object.keys(data.top_weapons_by_category).length === 0) {
            statsOutput.innerHTML += '<p>No weapon stats found for the specified categories (AR, SR, DMR, SMG, Shotgun) or player has no relevant data for this season.</p>';
            return;
        }
        for (const category in data.top_weapons_by_category) {
            const weapon = data.top_weapons_by_category[category];
            const weaponDiv = document.createElement('div');
            weaponDiv.className = 'stats-category';
            weaponDiv.innerHTML = `
                <h3>Top ${escapeHtml(weapon.category)}</h3>
                <p><strong>Weapon:</strong> ${escapeHtml(weapon.weapon_id.replace("Item_Weapon_", "").replace("_C",""))}</p>
                <p><strong>Total Damage:</strong> ${weapon.total_damage.toFixed(2)}</p>
                <p><strong>Kills:</strong> ${weapon.kills}</p>
                <p><strong>Damage Per Match (DPM):</strong> ${weapon.dpm.toFixed(2)}</p>
            `;
            statsOutput.appendChild(weaponDiv);
        }
    }

    function displayTeamPerformance(data) {
        teamIdentificationMessage.textContent = `Team Identification: ${escapeHtml(data.identified_team_method)}`;
        teamIdentificationMessage.style.display = 'block';
        
        destroyCharts(); 

        if (!data.team_performance_stats || data.team_performance_stats.length === 0) {
            teamChartsContainer.innerHTML = '<p>No team performance data to display. The identified team might have no recent common matches or the player is solo.</p>';
            return;
        }

        data.team_performance_stats.forEach(teammate => {
            if (teammate.matches_played_together > 0) {
                const chartContainer = document.createElement('div');
                chartContainer.className = 'chart-container';
                
                const title = document.createElement('h3');
                title.textContent = `Teammate: ${escapeHtml(teammate.teammate_account_id)}`;
                chartContainer.appendChild(title);

                const canvas = document.createElement('canvas');
                chartContainer.appendChild(canvas);
                teamChartsContainer.appendChild(chartContainer);

                const maxAssumedRank = 50; 
                let normalizedRankScore = (maxAssumedRank - teammate.avg_match_rank) / maxAssumedRank * 100;
                normalizedRankScore = Math.max(0, Math.min(100, normalizedRankScore)); 

                const chartData = {
                    labels: ['Avg Kills', 'Avg Damage', 'Avg Survival (s)', 'Avg Placement Score', 'Avg Assists'],
                    datasets: [{
                        label: `Stats (Matches: ${teammate.matches_played_together})`,
                        data: [
                            teammate.avg_kills,
                            teammate.avg_damage_dealt,
                            teammate.avg_survival_time_seconds,
                            normalizedRankScore, 
                            teammate.avg_assists
                        ],
                        backgroundColor: 'rgba(255, 204, 0, 0.2)', 
                        borderColor: '#ffcc00', 
                        pointBackgroundColor: '#ffcc00',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#ffcc00'
                    }]
                };
                
                const newChart = new Chart(canvas, {
                    type: 'radar',
                    data: chartData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false, 
                        scales: {
                            r: {
                                angleLines: { color: 'rgba(255, 255, 255, 0.3)' },
                                grid: { color: 'rgba(255, 255, 255, 0.3)' },
                                pointLabels: { color: '#ffffff', font: { size: 11 } },
                                ticks: { color: '#ffffff', backdropColor: 'rgba(0,0,0,0.5)', font: { size: 10 } }
                            }
                        },
                        plugins: { legend: { labels: { color: '#ffffff', font: {size: 12} } } }
                    }
                });
                currentCharts.push(newChart);
            } else {
                 const noDataMessage = document.createElement('p');
                 noDataMessage.textContent = `No common matches found with teammate ${escapeHtml(teammate.teammate_account_id)} in the analyzed set.`;
                 noDataMessage.className = 'info-message'; 
                 teamChartsContainer.appendChild(noDataMessage);
            }
        });
    }

    function displayOverallTeamStats(data) {
        overallTeamStatsOutput.innerHTML = ''; 
        overallTeamStatsMessage.style.display = 'none';
        overallTeamErrorDisplay.style.display = 'none'; 

        if (data.overall_stats && data.overall_stats.message) {
            overallTeamStatsMessage.textContent = escapeHtml(data.overall_stats.message);
            overallTeamStatsMessage.style.display = 'block';
        }

        if (data.overall_stats && data.overall_stats.matches_played_as_full_team > 0) {
            const stats = data.overall_stats;
            const content = `
                <p><strong>Matches Played as Full Team:</strong> ${stats.matches_played_as_full_team}</p>
                <p><strong>Average Team Kills per Match:</strong> ${stats.avg_team_kills.toFixed(2)}</p>
                <p><strong>Average Team Damage per Match:</strong> ${stats.avg_team_damage.toFixed(2)}</p>
                <p><strong>Average Team Survival Time:</strong> ${stats.avg_team_survival_time.toFixed(2)} seconds</p>
                <p><strong>Average Team Match Rank:</strong> ${stats.avg_team_match_rank.toFixed(2)}</p>
            `;
            overallTeamStatsOutput.innerHTML = content;
        } else if (data.overall_stats && data.overall_stats.matches_played_as_full_team === 0) {
            if (overallTeamStatsMessage.textContent && !overallTeamStatsMessage.textContent.toLowerCase().includes("no recent matches") && !overallTeamStatsMessage.textContent.toLowerCase().includes("not enough team members") && !overallTeamStatsMessage.textContent.toLowerCase().includes("no valid team identified")) {
                 overallTeamStatsOutput.innerHTML = '<p>No overall team stats available based on recent matches as a full unit.</p>';
            } else if (!overallTeamStatsMessage.textContent) { 
                overallTeamStatsOutput.innerHTML = '<p>No overall team stats available based on recent matches as a full unit.</p>';
            }
        } else if (!data.overall_stats) { 
            displayError("Overall team stats data is missing in the response.", overallTeamErrorDisplay);
        }
    }
    
    function destroyCharts() {
        currentCharts.forEach(chart => chart.destroy());
        currentCharts = [];
    }

    function displayError(message, element) {
        element.textContent = message;
        element.style.display = 'block';
    }

    function clearAllResults() {
        statsOutput.innerHTML = '';
        errorDisplay.style.display = 'none';
        
        teamIdentificationMessage.textContent = '';
        teamIdentificationMessage.style.display = 'none';
        teamChartsContainer.innerHTML = '';
        destroyCharts(); 
        teamErrorDisplay.textContent = '';
        teamErrorDisplay.style.display = 'none';
        teamPerformanceSection.style.display = 'none';

        overallTeamStatsMessage.textContent = '';
        overallTeamStatsMessage.style.display = 'none';
        overallTeamStatsOutput.innerHTML = '';
        overallTeamErrorDisplay.textContent = '';
        overallTeamErrorDisplay.style.display = 'none';
        overallTeamStatsSection.style.display = 'none';
    }

    function escapeHtml(unsafe) {
        if (unsafe === null || typeof unsafe === 'undefined') {
            return '';
        }
        return unsafe
             .toString()
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
