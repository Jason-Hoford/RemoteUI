"""ValueStringChange action — sets a string variable to a new value."""

from .action import Action


class ValueStringChange(Action):
    def __init__(self, id: int, value: str):
        self._value_id = id
        self._value = value

    def write(self, writer):
        new_value_id = writer.add_text(self._value)
        writer.add_value_string_change_action_operation(self._value_id, new_value_id)
