class ServerNotAvailableException(Exception):
    def __init__(self, message="Server not responding", innerEx=None):
        if innerEx is not None:
            super().__init__(message, innerEx)
        else:
            super().__init__(message)
