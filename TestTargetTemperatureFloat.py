import unittest

from numpy import float32, uint32
from numpy import isnan

from TargetTemperatureFloat import TargetTemperatureFloat, SingleNanPayLoad, TargetTemperatureError


class TestTargetTemperatureError(unittest.TestCase):
    def test(self):
        assert not TargetTemperatureError.has_value(0)
        assert not TargetTemperatureError.has_value(1)
        assert TargetTemperatureError.has_value(2)
        assert TargetTemperatureError.has_value(9)
        assert not TargetTemperatureError.has_value(10)


class TestTargetTemperatureFloat(unittest.TestCase):
    def test(self):
        assert not TargetTemperatureFloat.get_error(12.3)  # Normal number has no error
        assert not TargetTemperatureFloat.get_error(float32('nan'))  # Normal NAN has no error info

        nan_3 = SingleNanPayLoad.get_nan_with_pay_load(uint32(3))
        assert TargetTemperatureFloat.get_error(nan_3) == TargetTemperatureError.TargetTemperatureHigh

        nan_attenuation_too_high = TargetTemperatureFloat.get_nan_with_error(TargetTemperatureError.AttenuationTooHigh)
        assert TargetTemperatureFloat.get_error(nan_attenuation_too_high) == TargetTemperatureError.AttenuationTooHigh

        assert TargetTemperatureFloat.to_string(1.23) == '1.23'
        assert TargetTemperatureFloat.to_string(float32('nan')) == 'nan'
        assert TargetTemperatureFloat.to_string(nan_attenuation_too_high) == 'AttenuationTooHigh'


class TestSingleNanPayLoader(unittest.TestCase):
    def test(self):
        assert not SingleNanPayLoad.get_payload(float32(12.3))  # Normal float does not have payload
        assert SingleNanPayLoad.get_payload(float32('nan')) == 0  # A normal NAN has payload of 0

        nan_5 = SingleNanPayLoad.get_nan_with_pay_load(uint32(5))  # NAN with payload of 5
        assert isnan(nan_5)  # is a NAN,
        assert SingleNanPayLoad.get_payload(nan_5) == 5  # and has a payload of 5
