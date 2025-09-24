// Utility functions for battery visualization
export function safeFloat(val, def = 0) {
    if (val === 'N/A' || val === null || val === undefined || val === '') {
        return null; // Return null for missing values instead of 0
    }
    
    const num = parseFloat(val);
    if (isNaN(num)) return null;
    
    // Sanity checks for battery-related values to prevent display of unrealistic interpolated values
    // These ranges are based on typical laptop battery specifications
    if (num > 1000 || num < -100) return null; // Catch obviously wrong values
    
    return num;
}

export function formatDuration(secs) {
    if (!secs || secs === "N/A") return "N/A";
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    return `${h}h ${m}m`;
}

export function interpolate(value1, value2, ratio) {
    if (value1 === null || value2 === null) return null;
    return value1 + (value2 - value1) * ratio;
}
