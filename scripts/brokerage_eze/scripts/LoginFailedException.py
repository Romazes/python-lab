class LoginFailedException(Exception):
    def __init__(self, message="Login failed", innerEx=None):
        if innerEx is not None:
            super().__init__(message, innerEx)
        else:
            super().__init__(message)
