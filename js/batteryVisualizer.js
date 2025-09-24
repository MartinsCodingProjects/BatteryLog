// Main Battery Visualizer class - refactored and simplified
import { fetchData, parseData } from './dataHandler.js';
import { updateCurrentMetrics } from './uiComponents.js';
import { createHealthChart, createResourceChart, createScatter } from './chartRenderers.js';

export class BatteryVisualizer {
    constructor() {
        this.charts = {};
        this.settings = null;
        this.current_time_range = '1h';
        this.auto_refresh_enabled = true;
        this.auto_refresh_interval = null;
        this.uiState = null;
        this.initializeAsync();
    }
    
    async initializeAsync() {
        // Load settings asynchronously
        this.settings = await this.loadSettings();
        this.current_time_range = this.settings.time_range;
        this.auto_refresh_enabled = this.settings.auto_refresh;
        
        this.setupTimeControls();
        this.setupAutoRefresh();
        // Apply loaded settings to UI
        this.applySettingsToUI();
        // Load initial visualizations with settings
        this.updateVisualizations();
    }

    setupAutoRefresh() {
        // Create auto-refresh toggle button
        const refreshControls = document.querySelector('.time-controls');
        const autoRefreshBtn = document.createElement('button');
        autoRefreshBtn.id = 'autoRefresh';
        autoRefreshBtn.classList.add('auto-refresh');
        autoRefreshBtn.innerHTML = `⟳ Auto Refresh: ${this.auto_refresh_enabled ? 'On' : 'Off'}`;
        if (this.auto_refresh_enabled) autoRefreshBtn.classList.add('active');
        refreshControls.appendChild(autoRefreshBtn);

        // Add auto-refresh interval selector
        const intervalSelect = document.createElement('select');
        intervalSelect.id = 'refreshInterval';
        intervalSelect.classList.add('time-select');
        intervalSelect.style.display = this.auto_refresh_enabled ? 'block' : 'none';
        intervalSelect.innerHTML = `
            <option value="5000">5 seconds</option>
            <option value="10000">10 seconds</option>
            <option value="30000">30 seconds</option>
            <option value="60000">1 minute</option>
        `;
        intervalSelect.value = this.settings.refresh_interval;
        refreshControls.appendChild(intervalSelect);

        // Toggle auto-refresh
        autoRefreshBtn.addEventListener('click', () => {
            this.auto_refresh_enabled = !this.auto_refresh_enabled;
            this.settings.auto_refresh = this.auto_refresh_enabled;
            this.saveSettings();
            
            autoRefreshBtn.innerHTML = `⟳ Auto Refresh: ${this.auto_refresh_enabled ? 'On' : 'Off'}`;
            autoRefreshBtn.classList.toggle('active', this.auto_refresh_enabled);
            intervalSelect.style.display = this.auto_refresh_enabled ? 'block' : 'none';
            
            if (this.auto_refresh_enabled) {
                this.startAutoRefresh(parseInt(intervalSelect.value));
            } else {
                this.stopAutoRefresh();
            }
        });

        // Handle interval changes
        intervalSelect.addEventListener('change', (e) => {
            this.settings.refresh_interval = parseInt(e.target.value);
            this.saveSettings();
            
            if (this.auto_refresh_enabled) {
                this.startAutoRefresh(parseInt(e.target.value));
            }
        });
        
        // Start auto-refresh if enabled
        if (this.auto_refresh_enabled) {
            this.startAutoRefresh(this.settings.refresh_interval);
        }
    }

    startAutoRefresh(interval) {
        this.stopAutoRefresh(); // Clear any existing interval
        this.preserveUIState(); // Preserve UI state before refresh
        this.updateVisualizations(); // Update immediately
        this.auto_refresh_interval = setInterval(() => {
            console.log('Auto-refreshing visualizations...');
            this.preserveUIState(); // Preserve UI state before each refresh
            this.updateVisualizations();
            this.restoreUIState(); // Restore UI state after refresh
        }, interval);
    }

    stopAutoRefresh() {
        if (this.auto_refresh_interval) {
            clearInterval(this.auto_refresh_interval);
            this.auto_refresh_interval = null;
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
                this.current_time_range = daySelector.value || this.settings.custom_date;
            } else {
                daySelector.style.display = 'none';
                this.current_time_range = value;
            }
            
            this.settings.time_range = this.current_time_range;
            if (value === 'custom' && daySelector.value) {
                this.settings.custom_date = daySelector.value;
            }
            this.saveSettings();
            this.updateVisualizations();
        });

        daySelector.addEventListener('change', (e) => {
            this.current_time_range = e.target.value;
            this.settings.time_range = this.current_time_range;
            this.settings.custom_date = e.target.value;
            this.saveSettings();
            this.updateVisualizations();
        });
    }

    async updateVisualizations() {
        // Preserve and restore UI state
        this.preserveUIState();
        
        const rows = await fetchData(this.current_time_range);
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
        this.applySettingsToUI();
    }
    
    loadSettings() {
        const defaults = {
            time_range: '1h',
            custom_date: null,
            auto_refresh: true,
            refresh_interval: 60000 // 1 minute
        };
        
        try {
            // Load settings from user_settings.json via fetch
            return this.loadSettingsFromFile().then(settings => {
                return settings ? { ...defaults, ...settings.visualization } : defaults;
            }).catch(() => defaults);
        } catch (e) {
            console.warn('Failed to load settings:', e);
            return Promise.resolve(defaults);
        }
    }
    
    async loadSettingsFromFile() {
        try {
            const response = await fetch('http://localhost:8081/get_settings');
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.warn('Settings server not accessible, using defaults:', e);
        }
        return null;
    }
    
    async saveSettings() {
        try {
            const response = await fetch('http://localhost:8081/update_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.settings)
            });
            
            if (response.ok) {
                console.log('Settings saved successfully');
            } else {
                throw new Error('Failed to save settings');
            }
        } catch (e) {
            console.warn('Failed to save settings to server, using sessionStorage as fallback:', e);
            sessionStorage.setItem('batteryLogSettings', JSON.stringify(this.settings));
        }
    }
    
    applySettingsToUI() {
        const timeRange = document.getElementById('timeRange');
        const daySelector = document.getElementById('daySelector');
        
        // Set the time range selector to the correct value
        if (this.current_time_range.match(/^\d{4}-\d{2}-\d{2}$/)) {
            // If it's a date, set to custom and show day selector
            timeRange.value = 'custom';
            daySelector.style.display = 'block';
            daySelector.value = this.current_time_range;
        } else {
            // If it's a preset range, set accordingly
            timeRange.value = this.current_time_range;
            daySelector.style.display = 'none';
        }
        
        // Update auto-refresh UI
        const autoRefreshBtn = document.getElementById('autoRefresh');
        const intervalSelect = document.getElementById('refreshInterval');
        
        if (autoRefreshBtn) {
            autoRefreshBtn.innerHTML = `⟳ Auto Refresh: ${this.auto_refresh_enabled ? 'On' : 'Off'}`;
            autoRefreshBtn.classList.toggle('active', this.auto_refresh_enabled);
        }
        
        if (intervalSelect) {
            intervalSelect.style.display = this.auto_refresh_enabled ? 'block' : 'none';
            intervalSelect.value = this.settings.refresh_interval;
        }
    }
}
