from typing import NamedTuple


class Block(NamedTuple):
    min: float
    max: float


class EnforcedDict(dict):
    """ Dictionary which specifies object types for keys and values on
    instantiation.

    Enforcement of types occurs at instantiation, when key value
    pairs are added and when using the update method. In all other respects
    EnforcedDict objects behave identically to dict objects
    """
    def __init__(
            self,
            data: dict,
            key_type: type,
            value_type: type
    ):
        self._key_type = key_type
        self._value_type = value_type
        if data:
            for k, v in data.items():
                self.key_value_type_check(
                    k,
                    v,
                    self._key_type,
                    self._value_type
                )
            data = data
        else:
            data = tuple({})
        super(EnforcedDict, self).__init__(data)

    def key_value_type_check(
            self,
            key,
            value,
            key_type: type,
            value_type: type
    ):
        message = '{} type in key, value pair must be' \
                  ' {} for {} object, but {} was passed'.format
        if not isinstance(key, key_type):
            raise TypeError(message(
                'Key',
                key_type.__name__,
                type(self).__name__,
                type(key).__name__)
            )
        if not isinstance(value, value_type):
            raise TypeError(message(
                'Value',
                value_type.__name__,
                type(self).__name__,
                type(value).__name__)
            )

    def __setitem__(self, key, value):
        self.key_value_type_check(
            key,
            value,
            self._key_type,
            self._value_type
        )
        return super(EnforcedDict, self).__setitem__(key, value)

    def update(self, *args):
        for k, v in args[0].items():
            self.key_value_type_check(
                k,
                v,
                self._key_type,
                self._value_type
            )
        super(EnforcedDict, self).update(*args)
