// Chart creation and rendering functionality

// Detect rapid battery percentage changes that might indicate calibration issues
function detectRapidBatteryChanges(percentageData, timestamps, powerPluggedData) {
    const rapidChanges = [];
    const avgChangeRate = [];
    
    // Calculate average change rate over a sliding window
    const windowSize = Math.max(5, Math.floor(percentageData.length / 15)); // Larger adaptive window
    
    for (let i = 0; i < percentageData.length; i++) {
        if (i < Math.min(windowSize, 3)) {
            avgChangeRate.push(null);
            continue;
        }
        
        const window = percentageData.slice(Math.max(0, i - windowSize), i + 1);
        const timeWindow = timestamps.slice(Math.max(0, i - windowSize), i + 1);
        
        // Calculate average rate of change per minute
        let totalChange = 0;
        let totalTimeMinutes = 0;
        let validChanges = 0;
        
        for (let j = 1; j < window.length; j++) {
            if (window[j] != null && window[j-1] != null) {
                const change = Math.abs(window[j] - window[j-1]);
                const timeMinutes = (new Date(timeWindow[j]) - new Date(timeWindow[j-1])) / (1000 * 60);
                if (timeMinutes > 0 && change < 50) { // Ignore massive jumps when calculating average
                    totalChange += change;
                    totalTimeMinutes += timeMinutes;
                    validChanges++;
                }
            }
        }
        
        const avgRate = validChanges > 0 ? totalChange / totalTimeMinutes : 0;
        avgChangeRate.push(avgRate);
        
        // Check current change vs average AND absolute thresholds
        if (i > 0 && percentageData[i] != null && percentageData[i-1] != null) {
            const currentChange = Math.abs(percentageData[i] - percentageData[i-1]);
            const timeBetween = (new Date(timestamps[i]) - new Date(timestamps[i-1])) / (1000 * 60);
            const currentRate = timeBetween > 0 ? currentChange / timeBetween : 0;
            
            // Enhanced detection criteria
            const relativeThreshold = Math.max(avgRate * 2.5, 2); // 2.5x average or 2% per minute minimum
            const absoluteThreshold = 10; // 10% absolute change
            const extremeThreshold = 25; // 25% absolute change (always flag)
            
            // Flag if any of these conditions are met:
            let shouldFlag = false;
            let reason = "";
            
            if (currentChange >= extremeThreshold) {
                shouldFlag = true;
                reason = "Extreme drop (>25%)";
            } else if (currentChange >= absoluteThreshold && currentRate > relativeThreshold) {
                shouldFlag = true;
                reason = "Large sudden drop";
            } else if (currentRate > Math.max(avgRate * 4, 5) && currentChange > 7) {
                shouldFlag = true;
                reason = "Rate 4x higher than average";
            }
            
            // Special case: Power state change with large drop (common calibration issue)
            if (i > 0 && powerPluggedData && powerPluggedData[i] !== powerPluggedData[i-1] && 
                currentChange > 15) {
                shouldFlag = true;
                reason = "Large drop during power state change";
            }
            
            if (shouldFlag) {
                rapidChanges.push({
                    index: i,
                    timestamp: timestamps[i],
                    change: currentChange,
                    rate: currentRate,
                    avgRate: avgRate,
                    reason: reason,
                    powerStateChange: powerPluggedData ? (powerPluggedData[i] !== powerPluggedData[i-1]) : false
                });
            }
        }
    }
    
    console.log('Rapid battery changes detected:', rapidChanges);
    return rapidChanges;
}

// Create background color zones for plugged/unplugged states
function createChargingStateAnnotations(powerPluggedData, timestamps) {
    const annotations = [];
    let currentState = null;
    let stateStartIndex = 0;
    
    powerPluggedData.forEach((plugged, index) => {
        if (plugged !== currentState) {
            // State changed, create annotation for previous state
            if (currentState !== null && stateStartIndex < index - 1) {
                annotations.push({
                    type: 'box',
                    xMin: stateStartIndex,
                    xMax: index - 1,
                    backgroundColor: currentState ? 'rgba(46, 204, 64, 0.1)' : 'rgba(255, 65, 54, 0.1)', // Green for plugged, red for unplugged
                    borderColor: 'transparent',
                    label: {
                        enabled: false
                    }
                });
            }
            currentState = plugged;
            stateStartIndex = index;
        }
    });
    
    // Add final state annotation
    if (currentState !== null && stateStartIndex < powerPluggedData.length - 1) {
        annotations.push({
            type: 'box',
            xMin: stateStartIndex,
            xMax: powerPluggedData.length - 1,
            backgroundColor: currentState ? 'rgba(46, 204, 64, 0.1)' : 'rgba(255, 65, 54, 0.1)',
            borderColor: 'transparent',
            label: {
                enabled: false
            }
        });
    }
    
    return annotations;
}
export function createHealthChart(d) {
    // Debug time left data
    console.log('Time left data sample:', d.timeLeft.slice(0, 10));
    console.log('Non-null time left values:', d.timeLeft.filter(t => t != null).length);
    const validTimes = d.timeLeft.filter(t => t != null && !isNaN(t));
    console.log('Valid time left values:', validTimes.length);
    if (validTimes.length > 0) {
        const minTime = Math.min(...validTimes);
        const maxTime = Math.max(...validTimes);
        console.log('Time left range:', minTime, 'to', maxTime, 'seconds');
        console.log('Time left range formatted:', 
            `${Math.floor(minTime/3600)}:${Math.floor((minTime%3600)/60)}:${minTime%60}`, 
            'to', 
            `${Math.floor(maxTime/3600)}:${Math.floor((maxTime%3600)/60)}:${maxTime%60}`);
    }
    
    // Detect rapid battery changes
    const rapidChanges = detectRapidBatteryChanges(d.percentage, d.timestamps, d.powerPlugged);
    console.log('Detected rapid battery changes:', rapidChanges);
    
    // Create charging state annotations
    const chargingAnnotations = createChargingStateAnnotations(d.powerPlugged, d.timestamps);
    
    // Create points for rapid change indicators
    const rapidChangePoints = rapidChanges.map(change => ({
        x: change.index,
        y: d.percentage[change.index]
    }));
    
    return new Chart(document.getElementById('batteryHealthChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: d.timestamps.map(ts => new Date(ts).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            })),
            datasets: [
                {
                    label: 'Battery %',
                    data: d.percentage,
                    borderColor: '#0074D9',
                    backgroundColor: 'rgba(0, 116, 217, 0.1)',
                    yAxisID: 'percentage',
                    fill: false
                },
                {
                    label: 'Health %',
                    data: d.health,
                    borderColor: '#2ECC40',
                    backgroundColor: 'rgba(46, 204, 64, 0.1)',
                    yAxisID: 'percentage',
                    fill: false
                },
                {
                    label: 'Voltage',
                    data: d.voltage,
                    borderColor: '#FF4136',
                    backgroundColor: 'rgba(255, 65, 54, 0.1)',
                    yAxisID: 'voltage',
                    fill: false
                },
                {
                    label: 'Power Draw',
                    data: d.powerDraw,
                    borderColor: '#FF851B',
                    backgroundColor: 'rgba(255, 133, 27, 0.1)',
                    yAxisID: 'power',
                    fill: false
                },
                {
                    label: 'Time Left',
                    data: d.timeLeft,
                    borderColor: '#B10DC9',
                    backgroundColor: 'rgba(177, 13, 201, 0.1)',
                    yAxisID: 'timeLeft',
                    hidden: false,
                    fill: false
                },
                {
                    label: '⚠️ Calibration Issues',
                    data: rapidChangePoints,
                    backgroundColor: '#FFDC00',
                    borderColor: '#FF4500',
                    borderWidth: 3,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    showLine: false,
                    yAxisID: 'percentage',
                    type: 'scatter'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        afterBody: function(context) {
                            const dataIndex = context[0].dataIndex;
                            const change = rapidChanges.find(c => c.index === dataIndex);
                            if (change) {
                                const tooltipLines = [
                                    `🔍 Battery Calibration Issue Detected:`,
                                    `Reason: ${change.reason}`,
                                    `Change: ${change.change.toFixed(1)}%`,
                                    `Rate: ${change.rate.toFixed(2)}%/min`,
                                    `Expected: ${change.avgRate.toFixed(2)}%/min`
                                ];
                                
                                if (change.powerStateChange) {
                                    tooltipLines.push(`🔌 Power state changed during drop!`);
                                }
                                
                                tooltipLines.push(`⚠️ Likely calibration error!`);
                                return tooltipLines;
                            }
                            
                            // Show charging state
                            const isPlugged = d.powerPlugged[dataIndex];
                            if (isPlugged !== undefined) {
                                return [`🔌 Power: ${isPlugged ? 'Plugged In' : 'On Battery'}`];
                            }
                        }
                    }
                },
                annotation: {
                    annotations: chargingAnnotations
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time' },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                },
                percentage: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Percentage' },
                    min: 0,
                    max: 100
                },
                voltage: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Voltage (V)' }
                },
                power: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Power (W)' }
                },
                timeLeft: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Time Left (hh:mm:ss)' },
                    min: (() => {
                        const validTimes = d.timeLeft.filter(t => t != null && !isNaN(t));
                        if (validTimes.length === 0) return 0;
                        return Math.max(0, Math.min(...validTimes) - 600);
                    })(),
                    max: (() => {
                        const validTimes = d.timeLeft.filter(t => t != null && !isNaN(t));
                        if (validTimes.length === 0) return 3600; // Default 1 hour
                        return Math.max(...validTimes) + 600;
                    })(),
                    ticks: {
                        callback: function(value) {
                            const h = Math.floor(value / 3600);
                            const m = Math.floor((value % 3600) / 60);
                            const s = Math.floor(value % 60);
                            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
                        }
                    }
                }
            }
        }
    });
}

export function createResourceChart(d) {
    // Create charging state annotations for resource chart too
    const chargingAnnotations = createChargingStateAnnotations(d.powerPlugged, d.timestamps);
    
    return new Chart(document.getElementById('resourceChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: d.timestamps.map(ts => new Date(ts).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            })),
            datasets: [
                {
                    label: 'CPU %',
                    data: d.cpu,
                    borderColor: '#0074D9',
                    backgroundColor: 'rgba(0, 116, 217, 0.1)',
                    fill: false
                },
                {
                    label: 'RAM %',
                    data: d.ram,
                    borderColor: '#2ECC40',
                    backgroundColor: 'rgba(46, 204, 64, 0.1)',
                    fill: false
                },
                {
                    label: 'Disk %',
                    data: d.disk,
                    borderColor: '#FF4136',
                    backgroundColor: 'rgba(255, 65, 54, 0.1)',
                    fill: false
                },
                {
                    label: 'Drain Rate %/hr',
                    data: d.drainRate,
                    borderColor: '#FF851B',
                    backgroundColor: 'rgba(255, 133, 27, 0.1)',
                    yAxisID: 'drain',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        afterBody: function(context) {
                            const dataIndex = context[0].dataIndex;
                            const isPlugged = d.powerPlugged[dataIndex];
                            if (isPlugged !== undefined) {
                                return [`🔌 Power: ${isPlugged ? 'Plugged In (Charging/Plugged)' : 'On Battery (Draining)'}`];
                            }
                        }
                    }
                },
                annotation: {
                    annotations: chargingAnnotations
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Time' },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10,
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Percentage' },
                    min: 0,
                    max: 100
                },
                drain: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Drain Rate (%/hr)' }
                }
            }
        }
    });
}

export function createScatter(id, xData, yData, xLabel, yLabel) {
    return new Chart(document.getElementById(id).getContext('2d'), {
        type: 'scatter',
        data: {
            datasets: [{
                label: `${yLabel} vs ${xLabel}`,
                data: xData.map((x, i) => ({x: x, y: yData[i]})).filter(pt => pt.x != null && pt.y != null),
                backgroundColor: '#0074D9'
            }]
        },
        options: {
            scales: {
                x: { title: { display: true, text: xLabel } },
                y: { title: { display: true, text: yLabel } }
            }
        }
    });
}
