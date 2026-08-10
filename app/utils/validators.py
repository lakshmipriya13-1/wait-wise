import re

def validate_email(email):
    """
    Simple email validation regex pattern matching.
    """
    if not email:
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """
    Simple phone validation. Expects numeric, spaces, dashes, parentheses or plus sign.
    Length should be between 7 and 15 digits.
    """
    if not phone:
        return True # phone is optional in user model
    clean_phone = re.sub(r'[\s\(\)\-\+]', '', phone)
    return clean_phone.isdigit() and 7 <= len(clean_phone) <= 15

def validate_password_strength(password):
    """
    Ensure the password is at least 6 characters.
    """
    if not password or len(password) < 6:
        return False
    return True
