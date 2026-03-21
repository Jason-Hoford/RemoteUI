"""ValueFloatChange action — sets a float variable to a constant value."""

from .action import Action


class ValueFloatChange(Action):
    def __init__(self, id: int, value: float):
        self._value_id = id
        self._value = value

    def write(self, writer):
        writer.add_value_float_change_action_operation(self._value_id, self._value)
