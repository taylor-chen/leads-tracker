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
    """Input failed a business rule (not to be confused with pydantic's ValidationError)."""

    status_code = 422
    code = "validation_error"


class PayloadTooLargeError(DomainError):
    status_code = 413
    code = "payload_too_large"


class InvalidStateTransitionError(DomainError):
    """A lead state change not allowed by `LEAD_STATE_TRANSITIONS`."""

    status_code = 409
    code = "invalid_state_transition"


class AuthenticationError(DomainError):
    """Missing, invalid, expired or revoked credentials. Sent with `WWW-Authenticate`."""

    status_code = 401
    code = "not_authenticated"


class InvalidCurrentPasswordError(AuthenticationError):
    """Wrong current password on a password change, as opposed to a missing or expired session."""

    code = "invalid_current_password"
