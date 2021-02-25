from enum import Enum, unique
from struct import pack, unpack
from typing import Optional

from numpy import float32, isnan, uint32


@unique
class TargetTemperatureError(Enum):
    TargetTemperatureLow = 2
    TargetTemperatureHigh = 3
    InternalTemperatureLow = 4
    InternalTemperatureHigh = 5
    HeaterControlTemperatureLow = 6
    HeaterControlTemperatureHigh = 7
    EnergyTooLow = 8
    AttenuationTooHigh = 9

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


class SingleNanPayLoad:
    _nan_first = uint32(0x7fc00000)
    _nan_last = uint32(0x7FFFFFFF)
    _pay_load_max = uint32(_nan_last - _nan_first + 1)

    @staticmethod
    def _pay_load_is_valid(pay_load: uint32) -> bool:
        return pay_load <= SingleNanPayLoad._pay_load_max

    @staticmethod
    def get_nan_with_pay_load(pay_load: uint32) -> float32:
        if SingleNanPayLoad._pay_load_is_valid(pay_load):
            nan_uint32 = uint32(SingleNanPayLoad._nan_first + pay_load)
            nan_single = float32(unpack('f', pack('I', nan_uint32))[0])
            return nan_single
        else:
            raise ValueError("NAN pay load out of range!")

    @staticmethod
    def _has_payload(f: float32) -> bool:
        if not isnan(f):  # Normal float
            return False

        # Is NAN now
        nan_uint32 = uint32(unpack('I', pack('f', f))[0])

        if SingleNanPayLoad._nan_first <= nan_uint32 <= SingleNanPayLoad._nan_last:  # NAN has payload
            return True
        else:  # NAN does not have payload
            return False

    @staticmethod
    def get_payload(f: float32) -> Optional[uint32]:
        if SingleNanPayLoad._has_payload(f):
            nan_uint32 = uint32(unpack('I', pack('f', f))[0])
            return nan_uint32 - SingleNanPayLoad._nan_first
        else:
            return None


class TargetTemperatureFloat:
    @staticmethod
    def get_error(f) -> Optional[TargetTemperatureError]:
        payload = SingleNanPayLoad.get_payload(f)
        if payload:
            if TargetTemperatureError.has_value(payload):
                return TargetTemperatureError(payload)
            else:
                return None
        return None

    @staticmethod
    def get_nan_with_error(error: TargetTemperatureError):
        payload = error.value
        return SingleNanPayLoad.get_nan_with_pay_load(payload)

    @staticmethod
    def to_string(f):
        error = TargetTemperatureFloat.get_error(f)
        if error:
            return error.name
        else:
            return str(f)


