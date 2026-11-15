class FMError(Exception):
    """A safe, fixed public error code. Never carries input or DB credentials."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

