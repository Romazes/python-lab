class SessionNotFoundException(Exception):
    def __init__(self, message="Session not found."):
        super().__init__(message)