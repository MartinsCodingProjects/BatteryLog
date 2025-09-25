import pandas as pd
from datetime import datetime

def estimate_time_left_data_based(data):
    """
    Estimate the remaining time left on battery based on historical data from the battery_log.csv file.

    This function checks all entries from the csv for discrete intervals, 
    where data got logged without interruption and while running on battery.
    It then calculates the average drain rate (in % per minute) for each of these intervals, 
    calculates a weighted average drain rate based on all intervals 
    (weighted by their duration, and making the newer intervals more important).
    Finally, it estimates the remaining time left based on the current battery percentage and the average drain rate.
    
    Returns:
        dict: Contains 'time_left_minutes', 'confidence', 'intervals_used', 'average_drain_rate'
    """

    result = get_weighted_average_drain_rate(data)
    if result is None:
        return {
            'time_left_minutes': None,
            'confidence': 0,
            'intervals_used': 0,
            'average_drain_rate': None,
            'interval_details': []
        }
    
    average_drain_rate, confidence, intervals_used, interval_details = result
    current_battery_percent = data['percentage'].iloc[-1]  # read latest battery percentage from data in battery_log.csv
    
    if average_drain_rate is not None and average_drain_rate > 0:
        time_left = current_battery_percent / average_drain_rate  # in minutes
        return {
            'time_left_minutes': time_left,
            'confidence': confidence,
            'intervals_used': intervals_used,
            'average_drain_rate': average_drain_rate,
            'interval_details': interval_details
        }
    
    return {
        'time_left_minutes': None,
        'confidence': 0,
        'intervals_used': intervals_used,
        'average_drain_rate': None,
        'interval_details': interval_details
    }

def get_weighted_average_drain_rate(data):
    """
    Calculate a weighted average drain rate (% per minute) from historical battery data.

    This function identifies discrete intervals in the data where the system was running on battery power
    without interruptions. It calculates the drain rate for each interval and then computes a weighted
    average, giving more importance to longer intervals and more recent data.
    
    Returns:
        tuple: (average_drain_rate, confidence_score, num_intervals) or None if no valid intervals
    """
    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
        data['timestamp'] = pd.to_datetime(data['timestamp'])
    
    intervals = []
    start_idx = None
    max_gap_minutes = 5  # Maximum gap between data points to consider continuous

    for i in range(1, len(data)):
        current_plugged = data['power_plugged'].iloc[i]
        prev_plugged = data['power_plugged'].iloc[i-1]
        
        # Check for time gap (data interruption)
        time_gap = (data['timestamp'].iloc[i] - data['timestamp'].iloc[i-1]).total_seconds() / 60
        
        if current_plugged == False and prev_plugged == False and time_gap <= max_gap_minutes:
            if start_idx is None:
                start_idx = i - 1
        else:
            if start_idx is not None:
                end_idx = i - 1
                if end_idx > start_idx:
                    intervals.append((start_idx, end_idx))
                start_idx = None

    # Handle case where data ends while on battery
    if start_idx is not None and start_idx < len(data) - 1:
        intervals.append((start_idx, len(data) - 1))

    if not intervals:
        return None

    drain_rates = []
    weights = []
    durations = []
    recent_weight_multiplier = []

    # Use only the last 10 intervals for more recent/relevant data
    recent_intervals = intervals[-10:] if len(intervals) > 10 else intervals
    total_intervals = len(recent_intervals)
    
    for i, (start, end) in enumerate(recent_intervals):
        start_percent = data['percentage'].iloc[start]
        end_percent = data['percentage'].iloc[end]
        start_time = data['timestamp'].iloc[start]
        end_time = data['timestamp'].iloc[end]
        time_diff = (end_time - start_time).total_seconds() / 60  # in minutes

        # Only consider intervals with meaningful duration and battery drain
        if time_diff >= 2 and start_percent > end_percent and (start_percent - end_percent) >= 0.5:
            drain_rate = (start_percent - end_percent) / time_diff  # % per minute
            
            # Weight by duration (longer intervals are more reliable)
            duration_weight = min(time_diff, 120)  # Cap at 2 hours to prevent single long intervals from dominating
            
            # Recent intervals get exponentially higher weight
            recency_weight = pow(2, i)  # Exponential increase: 1, 2, 4, 8, 16...
            
            # Combined weight
            combined_weight = duration_weight * recency_weight
            
            drain_rates.append(drain_rate)
            weights.append(combined_weight)
            durations.append(time_diff)
            recent_weight_multiplier.append(recency_weight)

    if not drain_rates:
        return None

    # Calculate weighted average
    weighted_average = sum(rate * weight for rate, weight in zip(drain_rates, weights)) / sum(weights)
    
    # Prepare interval details for frontend
    interval_details = []
    for i, (start, end) in enumerate(recent_intervals):
        if i < len(drain_rates):  # Only include intervals that were actually used
            interval_details.append({
                'start_time': data['timestamp'].iloc[start].isoformat(),
                'end_time': data['timestamp'].iloc[end].isoformat(),
                'duration_minutes': durations[i],
                'data_points': end - start + 1,
                'start_percentage': float(data['percentage'].iloc[start]),
                'end_percentage': float(data['percentage'].iloc[end]),
                'drain_rate': drain_rates[i],
                'weight': weights[i]
            })
    
    # Calculate confidence score based on:
    # 1. Number of intervals
    # 2. Total duration of data
    # 3. Consistency of drain rates (lower variance = higher confidence)
    total_duration = sum(durations)
    num_intervals = len(drain_rates)
    
    # Variance in drain rates (normalized)
    if len(drain_rates) > 1:
        variance = sum((rate - weighted_average) ** 2 for rate in drain_rates) / len(drain_rates)
        normalized_variance = min(variance / weighted_average, 1.0) if weighted_average > 0 else 1.0
    else:
        normalized_variance = 0.5  # Moderate confidence for single interval
    
    # Confidence factors
    interval_confidence = min(num_intervals / 5.0, 1.0)  # Max confidence at 5+ intervals
    duration_confidence = min(total_duration / 60.0, 1.0)  # Max confidence at 60+ minutes
    consistency_confidence = 1.0 - normalized_variance  # Higher consistency = higher confidence
    
    # Overall confidence (0-1 scale)
    confidence = (interval_confidence * 0.4 + duration_confidence * 0.3 + consistency_confidence * 0.3)
    
    return weighted_average, confidence, num_intervals, interval_details

def estimate_time_on_full_battery(data):
    """
    Estimate the total time the battery can last on a full charge based on historical data.

    This function calculates the average drain rate (% per minute) from historical data
    and uses it to estimate how long the battery would last if it were fully charged.
    
    Returns:
        dict: Contains 'full_battery_time_minutes', 'confidence', 'intervals_used', 'average_drain_rate'
    """
    result = get_weighted_average_drain_rate(data)
    if result is None:
        return {
            'full_battery_time_minutes': None,
            'confidence': 0,
            'intervals_used': 0,
            'average_drain_rate': None,
            'interval_details': []
        }
    
    average_drain_rate, confidence, intervals_used, interval_details = result
    
    if average_drain_rate is not None and average_drain_rate > 0:
        total_time_on_full_battery = 100 / average_drain_rate  # in minutes
        return {
            'full_battery_time_minutes': total_time_on_full_battery,
            'confidence': confidence,
            'intervals_used': intervals_used,
            'average_drain_rate': average_drain_rate,
            'interval_details': interval_details
        }
    
    return {
        'full_battery_time_minutes': None,
        'confidence': 0,
        'intervals_used': intervals_used,
        'average_drain_rate': None,
        'interval_details': interval_details
    }


def estimate_time_left_last_interval(data):
    """
    Estimate time left based only on the most recent battery interval.
    
    Returns:
        dict: Contains 'time_left_minutes', 'confidence', 'drain_rate' based on last interval only
    """
    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
        data['timestamp'] = pd.to_datetime(data['timestamp'])
    
    # Find the most recent battery interval (even if it's currently ongoing)
    intervals = []
    start_idx = None
    max_gap_minutes = 5
    
    # First, find all battery intervals (same logic as main function)
    for i in range(1, len(data)):
        current_plugged = data['power_plugged'].iloc[i]
        prev_plugged = data['power_plugged'].iloc[i-1]
        
        # Check for time gap (data interruption)
        time_gap = (data['timestamp'].iloc[i] - data['timestamp'].iloc[i-1]).total_seconds() / 60
        
        if current_plugged == False and prev_plugged == False and time_gap <= max_gap_minutes:
            if start_idx is None:
                start_idx = i - 1
        else:
            if start_idx is not None:
                end_idx = i - 1
                if end_idx > start_idx:
                    intervals.append((start_idx, end_idx))
                start_idx = None

    # Handle case where data ends while on battery
    if start_idx is not None and start_idx < len(data) - 1:
        intervals.append((start_idx, len(data) - 1))
    
    # If no intervals found, try to find any recent battery usage
    if not intervals:
        # Look for any battery usage in recent data
        battery_indices = []
        for i in range(len(data)):
            if data['power_plugged'].iloc[i] == False:
                battery_indices.append(i)
        
        if len(battery_indices) >= 2:
            # Use the last few battery data points
            start_idx = battery_indices[-min(len(battery_indices), 10)]  # Last 10 or fewer
            end_idx = battery_indices[-1]
            intervals = [(start_idx, end_idx)]
    
    if not intervals:
        return {
            'time_left_minutes': None,
            'confidence': 0,
            'drain_rate': None,
            'debug': 'No battery intervals found'
        }
    
    # Use the last (most recent) interval
    start, end = intervals[-1]
    start_percent = data['percentage'].iloc[start]
    end_percent = data['percentage'].iloc[end]
    current_percent = data['percentage'].iloc[-1]
    start_time = data['timestamp'].iloc[start]
    end_time = data['timestamp'].iloc[end]
    time_diff = (end_time - start_time).total_seconds() / 60  # in minutes
    
    # More lenient requirements for last interval
    if time_diff >= 1 and start_percent > end_percent and (start_percent - end_percent) >= 0.1:
        drain_rate = (start_percent - end_percent) / time_diff  # % per minute
        time_left = current_percent / drain_rate if drain_rate > 0 else None
        
        # Confidence based on interval duration and battery drop
        duration_confidence = min(time_diff / 15.0, 1.0)  # Max confidence at 15+ minutes
        drop_confidence = min((start_percent - end_percent) / 2.0, 1.0)  # Max confidence at 2%+ drop
        confidence = (duration_confidence + drop_confidence) / 2
        
        return {
            'time_left_minutes': time_left,
            'confidence': confidence,
            'drain_rate': drain_rate,
            'debug': f'Interval: {start}-{end}, Duration: {time_diff:.1f}min, Drop: {start_percent-end_percent:.1f}%',
            'interval_details': [{
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': time_diff,
                'data_points': end - start + 1,
                'start_percentage': float(start_percent),
                'end_percentage': float(end_percent),
                'drain_rate': drain_rate,
                'weight': 1.0,
                'is_latest': True
            }]
        }
    
    return {
        'time_left_minutes': None,
        'confidence': 0,
        'drain_rate': None,
        'debug': f'Invalid interval: Duration: {time_diff:.1f}min, Drop: {start_percent-end_percent:.1f}%',
        'interval_details': []
    }

def estimate_full_battery_last_interval(data):
    """
    Estimate full battery time based only on the most recent battery interval.
    
    Returns:
        dict: Contains 'full_battery_time_minutes', 'confidence', 'drain_rate'
    """
    last_interval_result = estimate_time_left_last_interval(data)
    
    if last_interval_result['drain_rate'] is not None and last_interval_result['drain_rate'] > 0:
        full_battery_time = 100 / last_interval_result['drain_rate']  # in minutes
        return {
            'full_battery_time_minutes': full_battery_time,
            'confidence': last_interval_result['confidence'],
            'drain_rate': last_interval_result['drain_rate'],
            'interval_details': last_interval_result.get('interval_details', [])
        }
    
    return {
        'full_battery_time_minutes': None,
        'confidence': 0,
        'drain_rate': None,
        'interval_details': last_interval_result.get('interval_details', [])
    }

def get_battery_estimations(data):
    """
    Get comprehensive battery time estimations based on historical data.
    
    Returns:
        dict: Contains both averaged and last-interval estimations
    """
    time_left_result = estimate_time_left_data_based(data)
    full_battery_result = estimate_time_on_full_battery(data)
    
    # New: Last interval estimations
    time_left_last = estimate_time_left_last_interval(data)
    full_battery_last = estimate_full_battery_last_interval(data)
    
    current_percentage = data['percentage'].iloc[-1] if len(data) > 0 else 0
    
    return {
        'current_percentage': current_percentage,
        'time_left': time_left_result,
        'full_battery': full_battery_result,
        'time_left_last_interval': time_left_last,
        'full_battery_last_interval': full_battery_last,
        'timestamp': data['timestamp'].iloc[-1].isoformat() if len(data) > 0 else None
    }