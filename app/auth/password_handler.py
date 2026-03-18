from passlib.context import CryptContext

# bcrypt is the industry standard for password hashing
# auto means it always uses the best available scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    The hash includes the salt — no need to store salt separately.

    Args:
        plain_password: The raw password from the user.

    Returns:
        Bcrypt hashed string (60 chars).
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a stored bcrypt hash.
    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password:  Raw password from login request.
        hashed_password: Stored hash from the database.

    Returns:
        True if match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)