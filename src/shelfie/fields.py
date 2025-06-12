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
        elif self.default is not None:
            return self.default
        else:
            raise ValueError("Either a value must be provided or default or default_factory must be set for this field.")

    def __str__(self):
        return f"Field({self.name})"


def _today():
    return datetime.now().strftime("%Y-%m-%d")

def _now():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# Convenience functions for common field types
def DateField(name: str):
    """Field that defaults to today's date."""
    return Field(name, default_factory=_today)


def TimestampField(name: str):
    """Field that defaults to current timestamp."""
    return Field(name, default_factory=_now)
