class CallerPackageException(Exception):
    def __init__(self, message="Failed to get the caller package directory"):
        self.message = message
        super().__init__(self.message)


class MissingHeaderException(Exception):
    def __init__(self, header_name, message="Missing required header"):
        self.header_name = header_name
        self.message = f"{message}: {header_name}"
        super().__init__(self.message)