from passlib.context import CryptContext

# Define a single pwd_context instance
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Returns hashed password using pwd_context.hash()
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Returns boolean using pwd_context.verify()
    """
    return pwd_context.verify(plain_password, hashed_password)
