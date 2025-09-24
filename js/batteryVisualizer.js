// Main Battery Visualizer class - refactored and simplified
import { fetchData, parseData } from './dataHandler.js';
import { updateCurrentMetrics } from './uiComponents.js';
import { createHealthChart, createResourceChart, createScatter } from './chartRenderers.js';

export class BatteryVisualizer {
    constructor() {
        this.charts = {};
        this.currentTimeRange = '24h';
        this.autoRefreshEnabled = false;
        this.autoRefreshInterval = null;
        this.uiState = null;
        this.setupTimeControls();
        this.setupAutoRefresh();
    }

    setupAutoRefresh() {
        // Create auto-refresh toggle button
        const refreshControls = document.querySelector('.time-controls');
        const autoRefreshBtn = document.createElement('button');
        autoRefreshBtn.id = 'autoRefresh';
        autoRefreshBtn.classList.add('auto-refresh');
        autoRefreshBtn.innerHTML = '⟳ Auto Refresh: Off';
        refreshControls.appendChild(autoRefreshBtn);

        // Add auto-refresh interval selector
        const intervalSelect = document.createElement('select');
        intervalSelect.id = 'refreshInterval';
        intervalSelect.classList.add('time-select');
        intervalSelect.style.display = 'none';
        intervalSelect.innerHTML = `
            <option value="5000">5 seconds</option>
            <option value="10000">10 seconds</option>
            <option value="30000" selected>30 seconds</option>
            <option value="60000">1 minute</option>
        `;
        refreshControls.appendChild(intervalSelect);

        // Toggle auto-refresh
        autoRefreshBtn.addEventListener('click', () => {
            this.autoRefreshEnabled = !this.autoRefreshEnabled;
            autoRefreshBtn.innerHTML = `⟳ Auto Refresh: ${this.autoRefreshEnabled ? 'On' : 'Off'}`;
            autoRefreshBtn.classList.toggle('active', this.autoRefreshEnabled);
            intervalSelect.style.display = this.autoRefreshEnabled ? 'block' : 'none';
            
            if (this.autoRefreshEnabled) {
                this.startAutoRefresh(parseInt(intervalSelect.value));
            } else {
                this.stopAutoRefresh();
            }
        });

        // Handle interval changes
        intervalSelect.addEventListener('change', (e) => {
            if (this.autoRefreshEnabled) {
                this.startAutoRefresh(parseInt(e.target.value));
            }
        });
    }

    startAutoRefresh(interval) {
        this.stopAutoRefresh(); // Clear any existing interval
        this.preserveUIState(); // Preserve UI state before refresh
        this.updateVisualizations(); // Update immediately
        this.autoRefreshInterval = setInterval(() => {
            console.log('Auto-refreshing visualizations...');
            this.preserveUIState(); // Preserve UI state before each refresh
            this.updateVisualizations();
            this.restoreUIState(); // Restore UI state after refresh
        }, interval);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    setupTimeControls() {
        const timeRange = document.getElementById('timeRange');
        const daySelector = document.getElementById('daySelector');

        timeRange.addEventListener('change', (e) => {
            const value = e.target.value;
            if (value === 'custom') {
                daySelector.style.display = 'block';
                if (daySelector.options.length === 0) {
                    // Populate days from window.availableDays
                    window.availableDays?.forEach(day => {
                        const option = document.createElement('option');
                        option.value = day;
                        option.text = new Date(day).toLocaleDateString();
                        daySelector.appendChild(option);
                    });
                }
                this.currentTimeRange = daySelector.value;
            } else {
                daySelector.style.display = 'none';
                this.currentTimeRange = value;
            }
            this.updateVisualizations();
        });

        daySelector.addEventListener('change', (e) => {
            this.currentTimeRange = e.target.value;
            this.updateVisualizations();
        });
    }

    async updateVisualizations() {
        // Preserve and restore UI state
        this.preserveUIState();
        
        const rows = await fetchData(this.currentTimeRange);
        const d = parseData(rows);
        
        updateCurrentMetrics(d);

        // Destroy existing charts
        Object.values(this.charts).forEach(chart => chart?.destroy());
        
        // Create new charts
        this.charts.health = createHealthChart(d);
        this.charts.resources = createResourceChart(d);
        this.charts.powerCpu = createScatter('powerVsCpu', d.cpu, d.powerDraw, 'CPU %', 'Power Draw (W)');
        this.charts.drainLoad = createScatter('drainVsLoad', d.cpu.map((cpu, i) => cpu + d.ram[i] / 2), d.drainRate, 'System Load', 'Drain Rate (%/hr)');
        this.charts.voltageBattery = createScatter('voltageVsBattery', d.percentage, d.voltage, 'Battery %', 'Voltage (V)');
        this.charts.healthAnalysis = createScatter('healthAnalysis', d.drainRate, d.voltage, 'Drain Rate (%/hr)', 'Voltage (V)');
        
        // Restore UI state after update
        this.restoreUIState();
    }

    preserveUIState() {
        // Store current UI state
        const timeRange = document.getElementById('timeRange');
        const daySelector = document.getElementById('daySelector');
        
        this.uiState = {
            timeRangeValue: timeRange.value,
            dayRangeValue: daySelector.value,
            dayRangeVisible: daySelector.style.display !== 'none'
        };
    }

    restoreUIState() {
        // Restore UI state to match current selection
        const timeRange = document.getElementById('timeRange');
        const daySelector = document.getElementById('daySelector');
        
        if (this.uiState) {
            // Set the time range selector to the correct value
            if (this.currentTimeRange.match(/^\d{4}-\d{2}-\d{2}$/)) {
                // If it's a date, set to custom and show day selector
                timeRange.value = 'custom';
                daySelector.style.display = 'block';
                daySelector.value = this.currentTimeRange;
            } else {
                // If it's a preset range, set accordingly
                timeRange.value = this.currentTimeRange;
                daySelector.style.display = 'none';
            }
        }
    }
}
