// Data fetching and parsing functionality
import { safeFloat, interpolate } from './utils.js';

export async function fetchData(time_range = null) {
    const response = await fetch('battery_log.csv');
    const text = await response.text();
    console.log('CSV loaded, first 200 chars:', text.slice(0, 200));
    
    const rows = text.trim().split('\n').map(row => row.split(','));
    console.log(`Total rows: ${rows.length}`);
    
    // Get header and data separately
    const header = rows[0];
    const data = rows.slice(1);
    
    // Find timestamp column index
    const timestampIdx = header.indexOf('timestamp');
    if (timestampIdx === -1) {
        console.error('No timestamp column found');
        return rows;
    }

    // Parse timestamps and sort data
    const parsedData = data.map(row => ({
        timestamp: new Date(row[timestampIdx]),
        row
    })).sort((a, b) => a.timestamp - b.timestamp);

    // Group data by days for the selector
    const days = new Set();
    parsedData.forEach(item => {
        const day = item.timestamp.toISOString().split('T')[0];
        days.add(day);
    });
    window.availableDays = Array.from(days).sort();

    // Apply time range filter if provided
    let filteredData = parsedData;
    if (time_range) {
        const now = new Date();
        let startTime;
        
        switch(time_range) {
            case '1h':
                startTime = new Date(now - 60 * 60 * 1000);
                break;
            case '24h':
                startTime = new Date(now - 24 * 60 * 60 * 1000);
                break;
            case '7d':
                startTime = new Date(now - 7 * 24 * 60 * 60 * 1000);
                break;
            default:
                // Check if it's a specific date
                if (time_range.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    startTime = new Date(time_range);
                    const endTime = new Date(startTime);
                    endTime.setDate(endTime.getDate() + 1);
                    filteredData = parsedData.filter(item => 
                        item.timestamp >= startTime && item.timestamp < endTime);
                }
        }
        
        if (startTime && !time_range.match(/^\d{4}-\d{2}-\d{2}$/)) {
            filteredData = parsedData.filter(item => item.timestamp >= startTime);
        }
    }

    // Calculate time ranges
    const startTime = filteredData[0].timestamp;
    const endTime = filteredData[filteredData.length - 1].timestamp;
    const totalHours = (endTime - startTime) / (1000 * 60 * 60);
    
    // Target 200 samples evenly distributed across the time range
    const TARGET_SAMPLES = 200;
    const hoursBetweenSamples = totalHours / TARGET_SAMPLES;
    
    // Sample data points evenly across time with interpolation
    const sampledData = [];
    let currentTime = startTime;
    let currentIndex = 0;

    while (sampledData.length < TARGET_SAMPLES && currentTime <= endTime) {
        // Find the bracketing data points
        let beforeIndex = currentIndex;
        while (beforeIndex < filteredData.length && 
               filteredData[beforeIndex].timestamp <= currentTime) {
            beforeIndex++;
        }
        beforeIndex = Math.max(0, beforeIndex - 1);
        
        const afterIndex = Math.min(beforeIndex + 1, filteredData.length - 1);
        
        const before = filteredData[beforeIndex];
        const after = filteredData[afterIndex];
        
        // Calculate time gap
        const timeGap = after.timestamp - before.timestamp;
        const maxAllowedGap = 3 * 60 * 60 * 1000; // 3 hours max gap for interpolation
        
        if (timeGap > maxAllowedGap) {
            // Add a null point to create a visible gap in the charts
            sampledData.push(header.map(() => null));
        } else {
            // Interpolate between the points
            const ratio = (currentTime - before.timestamp) / (after.timestamp - before.timestamp);
            const interpolatedRow = before.row.map((val, idx) => {
                if (idx === timestampIdx) return currentTime.toISOString();
                
                // Special handling for time fields - don't interpolate, just use the closest value
                if (header[idx] === 'time_left_hms' || header[idx] === 'script_runtime_hms' || header[idx] === 'charge_time_min') {
                    return ratio < 0.5 ? before.row[idx] : after.row[idx];
                }
                
                // Special handling for sensitive battery metrics - use closest value instead of interpolating
                const sensitiveColumns = ['battery_health_pct', 'voltage_v', 'power_draw_w', 'cycle_count'];
                if (sensitiveColumns.includes(header[idx])) {
                    return ratio < 0.5 ? before.row[idx] : after.row[idx];
                }
                
                const num1 = parseFloat(before.row[idx]);
                const num2 = parseFloat(after.row[idx]);
                
                // Only interpolate if both values are valid numbers and reasonable
                if (isNaN(num1) || isNaN(num2)) {
                    return ratio < 0.5 ? before.row[idx] : after.row[idx];
                }
                
                // Sanity check for extreme values - don't interpolate if difference is too large
                if (Math.abs(num2 - num1) > Math.abs(num1) * 0.5) { // 50% change threshold
                    return ratio < 0.5 ? before.row[idx] : after.row[idx];
                }
                
                return interpolate(num1, num2, ratio).toString();
            });
            sampledData.push(interpolatedRow);
        }

        // Move time window forward
        currentTime = new Date(currentTime.getTime() + hoursBetweenSamples * 60 * 60 * 1000);
    }

    console.log(`Sampled ${sampledData.length} points evenly across ${totalHours.toFixed(1)} hours`);
    return [header, ...sampledData];
}

export function parseData(rows) {
    const header = rows[0];
    const data = rows.slice(1);
    const idx = name => header.indexOf(name);
    
    return {
        timestamps: data.map(row => row[idx('timestamp')]),
        percentage: data.map(row => safeFloat(row[idx('percentage')])),
        health: data.map(row => safeFloat(row[idx('battery_health_pct')])),
        voltage: data.map(row => safeFloat(row[idx('voltage_v')])),
        powerDraw: data.map(row => safeFloat(row[idx('power_draw_w')])),
        drainRate: data.map(row => safeFloat(row[idx('battery_drain_rate_pct_per_hour')])),
        cpu: data.map(row => safeFloat(row[idx('cpu_percent')])),
        ram: data.map(row => safeFloat(row[idx('ram_percent')])),
        disk: data.map(row => safeFloat(row[idx('disk_percent')])),
        temperature: data.map(row => safeFloat(row[idx('temperature_c')])),
        chargeTime: data.map(row => safeFloat(row[idx('charge_time_min')])),
        loadSeverity: data.map(row => row[idx('load_severity')] || 'Unknown'),
        voltageStatus: data.map(row => row[idx('voltage_status')] || 'Unknown'),
        cycleCount: data.map(row => safeFloat(row[idx('cycle_count')])),
        powerPlugged: data.map(row => row[idx('power_plugged')] === 'True'),
        timeLeft: data.map(row => {
            const t = row[idx('time_left_hms')];
            if (!t || t === 'N/A' || t === null || t === undefined) return null;
            try {
                const parts = t.split(':');
                if (parts.length !== 3) return null;
                const [h, m, s] = parts.map(Number);
                if (isNaN(h) || isNaN(m) || isNaN(s)) return null;
                const seconds = h * 3600 + m * 60 + s;
                return seconds;
            } catch {
                return null;
            }
        })
    };
}
