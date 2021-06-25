class CrawlerException(Exception):
    """A base exception class."""

    def __init__(self, msg):
        super().__init__(msg)


class NoActiveBrew(CrawlerException):
    """Raised when a user has no active homebrew of a certain type."""

    def __init__(self):
        super().__init__("You have no homebrew of this type active.")


class ExternalImportError(CrawlerException):
    """Raised when something fails to import."""

    def __init__(self, msg):
        super().__init__(msg)


class NotAllowed(CrawlerException):
    """Raised when a user tries to do something they are not allowed to do by role or dependency."""
    pass


class InvalidArgument(CrawlerException):
    """Raised when an argument is invalid."""
    pass


class EvaluationError(CrawlerException):
    """Raised when a cvar evaluation causes an error."""

    def __init__(self, original, expression=None):
        super().__init__(f"Error evaluating expression: {original}")
        self.original = original
        self.expression = expression


class SelectionException(CrawlerException):
    """A base exception for message awaiting exceptions to stem from."""
    pass


class NoSelectionElements(SelectionException):
    """Raised when get_selection() is called with no choices."""

    def __init__(self, msg=None):
        super().__init__(msg or "There are no choices to select from.")


class SelectionCancelled(SelectionException):
    """Raised when get_selection() is cancelled or times out."""

    def __init__(self):
        super().__init__("Selection timed out or was cancelled.")


class NoResultsFound(CrawlerException):
    """Raised when no results found in search functions."""
    def __init__(self):
        super().__init__("No results found, please try to different keyword.")