"""ValueIntegerChange action — sets an integer variable to a constant value."""

from .action import Action


class ValueIntegerChange(Action):
    def __init__(self, id: int, value: int):
        self._value_id = id
        self._value = value

    def write(self, writer):
        writer.add_value_integer_change_action_operation(self._value_id, self._value)
