import asyncio
import json
import logging
from typing import Optional

_DEVICE_INFO_MESSAGE = 'RENSON_DEVICE/JSON?'
_DEVICE_INFO_PORT = 49152
_DEVICE_INFO_TIMEOUT_SEC = 1

_LOGGER = logging.getLogger('device_info')


async def qstream_device(ip_address: str) -> Optional['QstreamDevice']:
    """Retrieve device info of Qstream device at specified address or network, with timeout.

    :param ip_address: The ip address or network broadcast address of the device.
    :return: Retrieved device info or None for no response from device.
    """

    transport, qstream_device_info = await _create_device_info_endpoint(ip_address)

    try:
        return await asyncio.wait_for(qstream_device_info, timeout=_DEVICE_INFO_TIMEOUT_SEC)
    except asyncio.TimeoutError:
        _LOGGER.debug('Timeout on retrieving device info with ip address: %s', ip_address)
        return None
    finally:
        transport.close()


async def _create_device_info_endpoint(ip_address: str) -> tuple[
        asyncio.BaseTransport, asyncio.Future['QstreamDevice']]:
    loop = asyncio.get_running_loop()
    qstream_device_info = loop.create_future()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: _QstreamDiscoverProtocol(qstream_device_info),
        local_addr=('0.0.0.0', 0),
        remote_addr=(ip_address, _DEVICE_INFO_PORT),
        allow_broadcast=True
    )

    return transport, qstream_device_info


class _QstreamDiscoverProtocol(asyncio.DatagramProtocol):
    def __init__(self, device_info_future: asyncio.Future['QstreamDevice']):
        self.device_info_future = device_info_future

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:  # type: ignore[override]
        transport.sendto(_DEVICE_INFO_MESSAGE.encode())

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            qstream_device_info = QstreamDevice(json.loads(data))
            self.device_info_future.set_result(qstream_device_info)
        except ValueError:
            _LOGGER.warning('Failed to parse data retrieved from address: %s', addr[0])


class QstreamDevice:
    """Holding the Qstream device info."""

    def __init__(self, device_info_dict: dict[str, str]):
        self._device_info_dict = device_info_dict

    @property
    def device(self) -> str:
        """Returns the (human-readable) name of the Qstream device."""
        return self._device_info_dict['Device']

    @property
    def firmware_version(self) -> str:
        """Returns the firmware version of the Qstream device."""
        return self._device_info_dict['FirmwareVersion']

    @property
    def ip(self) -> str:
        """Returns the ip-address of the Qstream device."""
        return self._device_info_dict['IP']

    @property
    def mac(self) -> str:
        """Returns the mac-address of the Qstream device."""
        return self._device_info_dict['MAC']

    def __repr__(self) -> str:
        return (f'QstreamDeviceInfo(device="{self.device}", firmware_version="{self.firmware_version}", ip="{self.ip}"'
                f', mac="{self.mac}")')

    def __eq__(self, other: object) -> bool:
        if isinstance(other, QstreamDevice):
            return self.device == other.device and self.firmware_version == other.firmware_version and self.ip == other.ip and self.mac == other.mac
        return False
