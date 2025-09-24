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
        timeRange: {
            start: firstTime.toLocaleString(),
            end: lastTime.toLocaleString(),
            hours: totalHours.toFixed(1)
        }
    };

    const grid = document.getElementById('current-metrics');
    grid.innerHTML = `
        <div class="metric-card time-range">
            <div class="metric-label">Analysis Period</div>
            <div class="metric-value">${latest.timeRange.hours}h</div>
            <div class="metric-details">
                From: ${latest.timeRange.start}<br>
                To: ${latest.timeRange.end}
            </div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Battery Level</div>
            <div class="metric-value">${latest.battery}%</div>
            <div class="metric-details">Current charge remaining in battery</div>
        </div>
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
