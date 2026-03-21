"""Base action interface — equivalent to Java's Action.java."""


class Action:
    """Base class for all actions."""

    def write(self, writer):
        raise NotImplementedError
