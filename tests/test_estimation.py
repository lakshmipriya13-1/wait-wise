from app.services.estimation_service import estimate_wait_time

def test_basic_wait_estimation():
    # 0 people ahead
    assert estimate_wait_time(0, 15) == 0
    
    # 1 person ahead, 15 minutes avg
    # 15 minutes, rounded to nearest 5 mins is 15
    assert estimate_wait_time(1, 15) == 15
    
    # 3 people ahead, 12 minutes avg
    # 3 * 12 = 36 -> rounded to nearest 5 mins is 35
    assert estimate_wait_time(3, 12) == 35
    
    # 1 person ahead, 3 minutes avg
    # 3 mins -> rounded to nearest 5 mins: wait, since it's <= 5, it should return at least 1 min.
    # Our formula does round(raw_estimate) -> round(3) = 3. Since it is <= 5, it is kept as 3.
    # Wait, let's look at the formula:
    # "If estimate > 5: estimate = 5 * round(estimate / 5)"
    # So if estimate is 3, it returns 3.
    assert estimate_wait_time(1, 3) == 3
