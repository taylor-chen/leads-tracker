class DomainError(Exception):
    """Base class for errors raised by the service layer and mapped to HTTP responses."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ValidationError(DomainError):
    status_code = 422
    code = "validation_error"


class PayloadTooLargeError(DomainError):
    status_code = 413
    code = "payload_too_large"


class InvalidStateTransitionError(DomainError):
    status_code = 409
    code = "invalid_state_transition"


class AuthenticationError(DomainError):
    status_code = 401
    code = "not_authenticated"
