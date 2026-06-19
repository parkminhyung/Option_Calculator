from datetime import datetime


def calculate_days_to_expiry(expiry_date):
    """만기일까지 남은 일수 계산 (만기일 포함)"""
    if not expiry_date:
        return None

    expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    today = datetime.now().date()
    return max((expiry - today).days + 1, 0)
