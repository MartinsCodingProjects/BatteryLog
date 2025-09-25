// UI components and metrics display
import { formatDuration } from './utils.js';

export function updateCurrentMetrics(d) {
    // Calculate time range
    const timestamps = d.timestamps.map(ts => new Date(ts));
    const firstTime = timestamps[0];
    const lastTime = timestamps[timestamps.length - 1];
    const totalHours = (lastTime - firstTime) / (1000 * 60 * 60);

    const latest = {
        battery: d.percentage[d.percentage.length - 1]?.toFixed(2),
        health: d.health[d.health.length - 1]?.toFixed(2),
        voltage: d.voltage[d.voltage.length - 1]?.toFixed(2),
        powerDraw: d.powerDraw[d.powerDraw.length - 1]?.toFixed(2),
        drainRate: d.drainRate[d.drainRate.length - 1]?.toFixed(2),
        timeLeft: d.timeLeft[d.timeLeft.length - 1],
        voltageStatus: d.voltageStatus[d.voltageStatus.length - 1],
        loadSeverity: d.loadSeverity[d.loadSeverity.length - 1],
        cycleCount: d.cycleCount[d.cycleCount.length - 1],
        time_range: {
            start: firstTime.toLocaleString(),
            end: lastTime.toLocaleString(),
            hours: totalHours.toFixed(1)
        }
    };

    // Load battery estimations
    loadBatteryEstimations().then(estimations => {
        console.log('Battery estimations loaded:', estimations); // Debug log
        displayMetrics(latest, estimations);
    }).catch(error => {
        console.warn('Failed to load battery estimations:', error);
        displayMetrics(latest, null);
    });
}

async function loadBatteryEstimations() {
    try {
        const response = await fetch('http://localhost:8081/get_estimations');
        if (response.ok) {
            return await response.json();
        }
    } catch (e) {
        console.warn('Estimations server not accessible:', e);
    }
    return null;
}

function displayMetrics(latest, estimations) {
    const grid = document.getElementById('current-metrics');
    
    // Format estimation time helper function
    function formatEstimationTime(minutes) {
        if (!minutes || isNaN(minutes)) return 'N/A';
        const hours = Math.floor(minutes / 60);
        const mins = Math.floor(minutes % 60);
        return `${hours}h ${mins}m`;
    }
    
    // Create interval details HTML
    function createIntervalDetailsHTML(intervals, isLatest = false, title = "Intervals Used") {
        if (!intervals || intervals.length === 0) return '';
        
        const intervalRows = intervals.map((interval, index) => {
            const startTime = new Date(interval.start_time).toLocaleString();
            const endTime = new Date(interval.end_time).toLocaleString();
            const latestClass = (isLatest || interval.is_latest) ? ' latest-interval' : '';
            const latestLabel = (isLatest || interval.is_latest) ? ' <span class="latest-label">LATEST</span>' : '';
            
            return `
                <tr class="interval-row${latestClass}">
                    <td>${index + 1}${latestLabel}</td>
                    <td>${startTime}</td>
                    <td>${endTime}</td>
                    <td>${interval.duration_minutes.toFixed(1)}</td>
                    <td>${interval.data_points}</td>
                    <td>${interval.start_percentage.toFixed(1)}% → ${interval.end_percentage.toFixed(1)}%</td>
                    <td>${(interval.drain_rate * 60).toFixed(2)}%/hr</td>
                </tr>
            `;
        }).join('');
        
        const detailsId = `details-${Math.random().toString(36).substr(2, 9)}`;
        
        return `
            <div class="interval-details-container">
                <button class="interval-toggle" onclick="toggleIntervalDetails('${detailsId}')">
                    📊 ${title} (${intervals.length}) 
                    <span class="toggle-arrow">▼</span>
                </button>
                <div id="${detailsId}" class="interval-details" style="display: none;">
                    <table class="interval-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Start Time</th>
                                <th>End Time</th>
                                <th>Duration (min)</th>
                                <th>Data Points</th>
                                <th>Battery Drop</th>
                                <th>Drain Rate</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${intervalRows}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Build estimations HTML
    let estimationsHTML = '';
    if (estimations && estimations.time_left) {
        const confidence = Math.round((estimations.time_left.confidence || 0) * 100);
        const confidenceColor = confidence > 70 ? '#2ECC40' : confidence > 40 ? '#FF851B' : '#FF4136';
        
        const lastConfidence = Math.round((estimations.time_left_last_interval?.confidence || 0) * 100);
        const lastConfidenceColor = lastConfidence > 70 ? '#2ECC40' : lastConfidence > 40 ? '#FF851B' : '#FF4136';
        
        estimationsHTML = `
            <div class="metric-card estimation">
                <div class="metric-label">🔋 Estimated Time Left (Average)</div>
                <div class="metric-value">${formatEstimationTime(estimations.time_left.time_left_minutes)}</div>
                <div class="metric-details">
                    Based on ${estimations.time_left.intervals_used} historical intervals<br>
                    <span style="color: ${confidenceColor}">Confidence: ${confidence}%</span>
                    ${createIntervalDetailsHTML(estimations.time_left.interval_details, false, "Historical Intervals")}
                </div>
            </div>
            <div class="metric-card estimation-last">
                <div class="metric-label">🔋 Time Left (Current Trend)</div>
                <div class="metric-value">${formatEstimationTime(estimations.time_left_last_interval?.time_left_minutes)}</div>
                <div class="metric-details">
                    Based on most recent battery usage<br>
                    <span style="color: ${lastConfidenceColor}">Confidence: ${lastConfidence}%</span>
                    ${estimations.time_left_last_interval?.debug ? '<br><small>Debug: ' + estimations.time_left_last_interval.debug + '</small>' : ''}
                    ${createIntervalDetailsHTML(estimations.time_left_last_interval?.interval_details, true, "Latest Interval")}
                </div>
            </div>
            <div class="metric-card estimation">
                <div class="metric-label">⚡ Full Battery Time (Average)</div>
                <div class="metric-value">${formatEstimationTime(estimations.full_battery.full_battery_time_minutes)}</div>
                <div class="metric-details">
                    Average runtime if fully charged<br>
                    <span style="color: ${confidenceColor}">Drain rate: ${(estimations.full_battery.average_drain_rate * 60).toFixed(2)}%/hr</span>
                    ${createIntervalDetailsHTML(estimations.full_battery.interval_details, false, "Historical Intervals")}
                </div>
            </div>
            <div class="metric-card estimation-last">
                <div class="metric-label">⚡ Full Battery Time (Current Trend)</div>
                <div class="metric-value">${formatEstimationTime(estimations.full_battery_last_interval?.full_battery_time_minutes)}</div>
                <div class="metric-details">
                    Based on current usage pattern<br>
                    <span style="color: ${lastConfidenceColor}">Drain rate: ${(estimations.full_battery_last_interval?.drain_rate * 60 || 0).toFixed(2)}%/hr</span>
                    ${estimations.full_battery_last_interval?.debug ? '<br><small>Debug: ' + estimations.full_battery_last_interval.debug + '</small>' : ''}
                    ${createIntervalDetailsHTML(estimations.full_battery_last_interval?.interval_details, true, "Latest Interval")}
                </div>
            </div>`;
    }
    
    grid.innerHTML = `
        <div class="metric-card time-range">
            <div class="metric-label">Analysis Period</div>
            <div class="metric-value">${latest.time_range.hours}h</div>
            <div class="metric-details">
                From: ${latest.time_range.start}<br>
                To: ${latest.time_range.end}
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Battery Level</div>
            <div class="metric-value">${latest.battery}%</div>
            <div class="metric-details">Current charge remaining in battery</div>
        </div>
        ${estimationsHTML}
        <div class="metric-card">
            <div class="metric-label">Battery Health</div>
            <div class="metric-value">${latest.health}%</div>
            <div class="metric-details">Maximum capacity vs. original design capacity</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Voltage</div>
            <div class="metric-value">${latest.voltage}V</div>
            <div class="metric-label">${latest.voltageStatus}</div>
            <div class="metric-details">Current electrical potential difference</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Power Draw</div>
            <div class="metric-value">${latest.powerDraw}W</div>
            <div class="metric-label">${latest.loadSeverity} Load</div>
            <div class="metric-details">Current power consumption rate - higher values drain battery faster</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Drain Rate</div>
            <div class="metric-value">${latest.drainRate}%/hr</div>
            <div class="metric-details">How fast battery percentage decreases per hour</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Time Left</div>
            <div class="metric-value">${formatDuration(latest.timeLeft)}</div>
            <div class="metric-details">Estimated runtime at current usage patterns</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Cycle Count</div>
            <div class="metric-value">${latest.cycleCount === 0 ? 'N/A' : latest.cycleCount}</div>
            <div class="metric-details">Total charge/discharge cycles completed</div>
        </div>
    `;
}

// Global function to toggle interval details (needed for onclick)
window.toggleIntervalDetails = function(detailsId) {
    const details = document.getElementById(detailsId);
    const button = details.previousElementSibling;
    const arrow = button.querySelector('.toggle-arrow');
    
    if (details.style.display === 'none') {
        details.style.display = 'block';
        arrow.textContent = '▲';
        button.classList.add('expanded');
    } else {
        details.style.display = 'none';
        arrow.textContent = '▼';
        button.classList.remove('expanded');
    }
};
