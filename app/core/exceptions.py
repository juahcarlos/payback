from fastapi import status


class LocalizedAPIException(Exception):
    def __init__(
            self,
            system_error_category: str = "internal_error",
            system_error_code: str = "error.internal",
            status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.system_error_category = system_error_category
        self.system_error_code = system_error_code
        self.status_code = status_code


class ClientError(LocalizedAPIException):
    def __init__(self, error_code: str = "vpn.error.header") -> None:
        super().__init__(
            system_error_category="client.error",
            system_error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class Error404(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="not.found",
            system_error_code="error.404.header",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ErrorCouponInvalid(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="error.invalid",
            system_error_code="vpn.order.error.invalid-coupon",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorCodeInvalid(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="code.invalid",
            system_error_code="api.code.invalid",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorCodeExpired(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="code.expired",
            system_error_code="api.code.expired",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorRecoveryRateLimited(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="code.recovery-limit",
            system_error_code="api.code.recovery-limit",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class ErrorCodeAlreadySent(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="code.already.sent",
            system_error_code="api.code.already.sent",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorEmailInvalid(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="vpn.recovery.error.invalid-email",
            system_error_code="vpn.recovery.error.invalid-email",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

class InternalError(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="internal_error",
            system_error_code="vpn.order.error.internal-error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ErrorAlreadyRegistered(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="vpn.order.error.email-alredy-registered",
            system_error_code="vpn.order.error.email-alredy-registered",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorAlreadySubscribed(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="error_subscription",
            system_error_code="vpn.order.error.already-subscribed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorIPAddressIsLocal(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="error.ip-is-local",
            system_error_code="error.ip-is-local",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorIPAddressIsInvalid(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="api.support.invalid_parameters",
            system_error_code="api.support.invalid_parameters",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ErrorBlacklistedEmail(LocalizedAPIException):
    def __init__(self) -> None:
        super().__init__(
            system_error_category="vpn.order.error.invalid-email-not-allowed",
            system_error_code="vpn.order.error.invalid-email-not-allowed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AuthError(LocalizedAPIException):
    def __init__(self, error_code: str = "auth.error.header") -> None:
        super().__init__(
            system_error_category="auth.error",
            system_error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthRateLimitedError(LocalizedAPIException):
    def __init__(self, error_code: str = "auth.error.rate-limited.header") -> None:
        super().__init__(
            system_error_category="auth.error.rate",
            system_error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
