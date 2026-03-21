"""ValueFloatExpressionChange action — sets a float variable to an expression result."""

from .action import Action


class ValueFloatExpressionChange(Action):
    def __init__(self, id: int, value: int):
        self._value_id = id
        self._value = value

    def write(self, writer):
        writer.add_value_float_expression_change_action_operation(self._value_id, self._value)
