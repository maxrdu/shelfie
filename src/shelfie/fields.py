from datetime import datetime


class Field:
    """Optional field class for defining field behavior and defaults."""

    def __init__(self, name: str, default=None, default_factory=None):
        self.name = name
        self.default = default
        self.default_factory = default_factory

    def get_value(self, provided_value=None):
        """Get the field value, using default if none provided."""
        if provided_value is not None:
            return provided_value
        elif self.default_factory is not None:
            return self.default_factory()
        else:
            return self.default


# Convenience functions for common field types
def DateField(name: str, format="%Y-%m-%d"):
    """Field that defaults to today's date."""
    return Field(name, default_factory=lambda: datetime.now().strftime(format))


def TimestampField(name: str):
    """Field that defaults to current timestamp."""
    return Field(
        name, default_factory=lambda: datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )
