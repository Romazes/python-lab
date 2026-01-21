class NetworkFailedException(Exception):
    def __init__(self, message="Failure in network", innerEx=None):
        if innerEx is not None:
            super().__init__(message, innerEx)
        else:
            super().__init__(message)
