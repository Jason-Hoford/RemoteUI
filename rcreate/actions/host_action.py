"""HostAction — triggers a host-side action callback."""

from .action import Action


class HostAction(Action):
    def __init__(self, id_or_name=None, metadata_id: int = -1, type: int = -1, value_id: int = -1):
        if isinstance(id_or_name, str):
            self._action_name = id_or_name
            self._action_id = -1
            self._type = type
            self._value_id = value_id
        else:
            self._action_id = id_or_name if id_or_name is not None else -1
            self._action_name = None
            self._value_id = metadata_id
            self._type = -1

    def write(self, writer):
        if self._action_name is None:
            if self._value_id != -1:
                writer._buffer.add_host_action_metadata(self._action_id, self._value_id)
            else:
                writer._buffer.add_host_action(self._action_id)
        else:
            text_id = writer.add_text(self._action_name)
            writer._buffer.add_host_named_action(text_id, self._type, self._value_id)
