class NotFoundError(Exception):
    """Raised when a resource is not found."""
    pass

class UnauthorizedError(Exception):
    """Raised when a user is not authorized to perform an action."""
    pass

class ValidationError(Exception):
    """Raised when a business rule or validation fails."""
    pass
