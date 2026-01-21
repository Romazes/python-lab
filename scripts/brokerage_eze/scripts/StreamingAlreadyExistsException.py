class StreamingAlreadyExistsException(Exception):
    def __init__(self, message="Streaming already exists", inner_ex=None):
        super().__init__(message)
        self.inner_ex = inner_ex