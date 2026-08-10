def estimate_wait_time(people_ahead, average_service_time, historical_factor=1.0, active_counters=1):
    """
    Calculates estimated waiting time in minutes.
    
    Formula:
      estimated_wait = (people_ahead * average_service_time * historical_factor) / active_counters
      
    This estimator is extensible and can incorporate other factors in the future.
    """
    if people_ahead <= 0:
        return 0
        
    # Standard formula
    raw_estimate = (people_ahead * average_service_time * historical_factor) / active_counters
    
    # We round it to the nearest 5 minutes for a clean, user-friendly presentation, 
    # but ensure it's at least 1 minute if there are people ahead.
    estimate = max(1, round(raw_estimate))
    
    # Rounding helper: e.g., if estimate is 12, round to 10 or 15. Let's do standard rounding to nearest 5 mins
    if estimate > 5:
        estimate = 5 * round(estimate / 5)
        
    return estimate
