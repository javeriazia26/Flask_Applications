import pyotp

from app.services.encryption_service import get_cipher


# =========================================================
# GENERATE SECRET
# =========================================================

def generate_secret():
    """
    Generate a unique secret key for the user's
    Authenticator App.
    """
    return pyotp.random_base32()


# =========================================================
# ENCRYPT SECRET
# =========================================================
def encrypt_secret(secret):
    
    if not secret:
        return None

    cipher = get_cipher()
    return cipher.encrypt(secret.encode()).decode()


# =========================================================
# DECRYPT SECRET
# =========================================================

def decrypt_data(encrypted_secret):
    if not encrypted_secret:
        return None

    cipher = get_cipher()
    return cipher.decrypt(encrypted_secret.encode()).decode()


# =========================================================
# DECRYPT SECRET
# =========================================================

def decrypt_secret(encrypted_secret):
    if not encrypted_secret:
        return None

    cipher = get_cipher()
    return cipher.decrypt(encrypted_secret.encode()).decode()


# =========================================================
# CREATE PROVISIONING URI
# =========================================================

def generate_provisioning_uri(secret, email, issuer_name="jirflux"):
    """
    Generate the URI that will be converted into
    a QR code for Google Authenticator,
    Microsoft Authenticator, etc.
    """

    totp = pyotp.TOTP(secret)

    return totp.provisioning_uri(
        name=email,
        issuer_name=issuer_name
    )


# =========================================================
# VERIFY AUTHENTICATOR CODE
# =========================================================

def verify_code(secret, code):
    """
    Verify the 6-digit code entered by the user.
    """

    if not secret or not code:
        return False

    totp = pyotp.TOTP(secret)

    return totp.verify(code)


# =========================================================
# GENERATE CURRENT CODE
# =========================================================

def generate_current_code(secret):
    """
    Generate the current TOTP code.

    This is mainly useful for testing.
    The user's Authenticator App generates
    the code during normal usage.
    """

    totp = pyotp.TOTP(secret)

    return totp.now()
