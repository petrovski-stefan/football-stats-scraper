# flake8: noqa


class SoupNoSuchElementException(Exception):
    """Raised when element is not found by Beautiful Soup parser."""

    pass


class InvalidOddsFormatException(ValueError):
    """Raised when odds do not follow XX.XX format."""

    pass


class InvalidScoreSumError(ValueError):
    """Raised when the sum of half-time and second-half scored goals is not equal to the full time score."""

    pass
