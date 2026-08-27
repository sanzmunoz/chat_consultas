from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(plain_password: str) -> str:
    """Generates secure bcrypt password hash."""
    return pwd_context.hash(plain_password)
