from langs.lang import langs


class MyCustomException(Exception):
    """
    Class for creating customized error messages,
    derived from Python's built-in Exception.
    """

    def __init__(self, name: str, error: str = "error", status_code: int = 200) -> None:
        self.name = name
        self.status_code = status_code
        self.error = error


def typed_error(
    lang: str = "en", name: str = "", error: str = "", status_code: int = 200
) -> MyCustomException:
    """
    Create MyCustomException instance based on Python Exception class,
    to generate error messages with custom name, message, and status code.
    Args:
        lang (str): Language code for localization, defaults to 'en'.
        name (str): Error key or name used for localization.
        error (str): Detailed error message.
        status_code (int): HTTP status code for the error, defaults to 200.
    Returns:
        MyCustomException: Exception instance derived from Python Exception.
    """
    name_ = langs(lang, name)
    if name_ == "":
        name_ = "Error unknown"
    res_mce = MyCustomException(
        name=name_,
        error=error,
        status_code=status_code,
    )
    return res_mce


def error_404(lang: str = "en") -> MyCustomException:
    """Return 404 error with."""
    return typed_error(lang, "error.404.header", "not.found", 404)


def internal_error(
    lang: str = "en", error: str = "", status_code: int = 200
) -> MyCustomException:
    """Return custom error with developer defined parameters and status."""
    return typed_error(lang, "vpn.order.error.internal-error", error, status_code)
