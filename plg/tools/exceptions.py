class MaxNodesExceededError(Exception):
    """Raised when the tree expansion exceeds the maximum number of nodes."""

    def __init__(
        self, message="Tree expansion exceeded the maximum limit of 50 nodes."
    ):
        self.message = message
        super().__init__(self.message)
