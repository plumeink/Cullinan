class CallerPackageException(Exception):
    def __init__(self, message="Failed to get the caller package directory"):
        self.message = message
        super().__init__(self.message)