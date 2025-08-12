from libs.exceptions import typed_error


def already_sent(lang):
    """Return error for already sent recovery request in given language."""
    return typed_error(
        lang, "vpn.recovery.error.allready-sent", "vpn.recovery.error.allready-sent"
    )


def blacklisted_email(lang):
    """Return error for blacklisted email address in given language."""
    return typed_error(
        lang,
        "vpn.order.error.invalid-email-not-allowed",
        "vpn.order.error.invalid-email-not-allowed",
    )
