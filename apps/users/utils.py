import secrets
import string
import re
from django.core.mail import EmailMessage

def send_email(subject, message, recipient_list, html_message=None):
    email = EmailMessage(
        subject=subject,
        body=message,
        from_email='noreply@yourdomain.com',
        to=recipient_list,
    )
    if html_message:
        email.content_subtype = "html"
    

    email.send(fail_silently=False)



def generate_random_code(length=6) -> str:
    # Create a pool of uppercase, lowercase letters, and digits
    characters = string.ascii_letters + string.digits
    # Generate cryptographically secure random code
    return ''.join(secrets.choice(characters) for _ in range(length))

def validate_password(password:str) -> tuple[bool, list]:
    """
    Check if the password meets the following criteria:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return not len(errors), errors