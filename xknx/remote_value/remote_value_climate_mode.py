"""
Module for managing an climate mode remote values.

DPT .
"""
from enum import Enum

from xknx.dpt import (
    DPTArray, DPTBinary, DPTControllerStatus, DPTHVACContrMode, DPTHVACMode,
    HVACOperationMode)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueClimateMode(RemoteValue):
    """Abstraction for remote value of KNX climate modes."""

    class ClimateModeType(Enum):
        """Implemented climate mode types."""

        CONTROLLER_STATUS = DPTControllerStatus
        HVAC_CONTR_MODE = DPTHVACContrMode
        HVAC_MODE = DPTHVACMode

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 device_name=None,
                 feature_name="Climate Mode",
                 climate_mode_type=None,
                 after_update_cb=None):
        """Initialize remote value of KNX climate mode."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address=group_address,
                         group_address_state=group_address_state,
                         sync_state=sync_state,
                         device_name=device_name,
                         feature_name=feature_name,
                         after_update_cb=after_update_cb)
        if not isinstance(climate_mode_type, self.ClimateModeType):
            raise ConversionError("invalid climate mode type",
                                  climate_mode_type=climate_mode_type, device_name=device_name, feature_name=feature_name)
        self._climate_mode_transcoder = climate_mode_type.value

    def supported_operation_modes(self):
        """Return a list of all supported operation modes."""
        return list(self._climate_mode_transcoder.SUPPORTED_MODES.values())

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(self._climate_mode_transcoder.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self._climate_mode_transcoder.from_knx(payload.value)


class _RemoteValueBinaryClimateMode(RemoteValue):
    """Base class for binary climate mode remote values."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 device_name=None,
                 feature_name="Climate Mode Binary",
                 after_update_cb=None,
                 operation_mode=None):
        """Initialize remote value of KNX DPT 1 representing a climate operation mode."""
        # pylint: disable=too-many-arguments
        if not isinstance(operation_mode, HVACOperationMode):
            raise ConversionError("Invalid operation mode type",
                                  operation_mode=operation_mode, device_name=device_name, feature_name=feature_name)
        if operation_mode not in self.supported_operation_modes():
            raise ConversionError("Operation mode not supported for binary mode object",
                                  operation_mode=operation_mode, device_name=device_name, feature_name=feature_name)
        self.operation_mode = operation_mode
        super().__init__(xknx,
                         group_address=group_address,
                         group_address_state=group_address_state,
                         sync_state=True,
                         device_name=device_name,
                         feature_name=feature_name,
                         after_update_cb=after_update_cb)

    @staticmethod
    def supported_operation_modes():
        """Return a list of the configured operation mode."""
        raise NotImplementedError('supported_operation_modes has to return a list')

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if isinstance(value, HVACOperationMode):
            # foreign operation modes will set the RemoteValue to False
            return DPTBinary(value == self.operation_mode)
        raise ConversionError("value invalid",
                              value=value, device_name=self.device_name, feature_name=self.feature_name)


class RemoteValueBinaryOperationMode(_RemoteValueBinaryClimateMode):
    """Abstraction for remote value of split up KNX climate modes."""

    @staticmethod
    def supported_operation_modes():
        """Return a list of the configured operation mode."""
        return [HVACOperationMode.COMFORT,
                HVACOperationMode.FROST_PROTECTION,
                HVACOperationMode.NIGHT,
                HVACOperationMode.STANDBY]

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.operation_mode
        if payload == DPTBinary(0):
            return None
        raise CouldNotParseTelegram("payload invalid",
                                    payload=payload, device_name=self.device_name, feature_name=self.feature_name)


class RemoteValueBinaryHeatCool(_RemoteValueBinaryClimateMode):
    """Abstraction for remote value of heat/cool controller mode."""

    @staticmethod
    def supported_operation_modes():
        """Return a list of the configured operation mode."""
        return [HVACOperationMode.HEAT,
                HVACOperationMode.COOL]

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.operation_mode
        if payload == DPTBinary(0):
            # return the other operation mode
            return next((_op for _op in self.supported_operation_modes() if _op is not self.operation_mode),
                        None)
        raise CouldNotParseTelegram("payload invalid",
                                    payload=payload, device_name=self.device_name, feature_name=self.feature_name)
