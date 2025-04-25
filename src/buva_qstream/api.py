import re

from aiohttp import ClientSession

from buva_qstream import QstreamDevice


class QstreamAPI:
    def __init__(self, device: QstreamDevice, client_session: ClientSession):
        self.device = device
        self.client_session = client_session

    async def actual_speed(self) -> str:
        return await self._retrieve_status_value("Qactual")

    async def selected_speed(self) -> str:
        return await self._retrieve_status_value("Qset")

    async def nominal_speed(self) -> str:
        return await self._retrieve_value("Qnom")

    async def air_quality_index(self) -> int:
        return int(await self._retrieve_value("AQI"))

    async def is_demand_control_enabled(self) -> bool:
        return await self._retrieve_status_value("DEMAND CONTROL") == "ON"

    async def set_demand_control_on(self) -> None:
        resp = await self.client_session.post(f"http://{self.device.ip}/Timer", data='{ "Value": "TIMER 0 MIN" }')
        resp.raise_for_status()

    async def set_speed(self, speed: int, timer_minutes: int = 30) -> None:
        timer_value = f"{timer_minutes} MIN" if timer_minutes > 0 else "CONT"
        resp = await self.client_session.post(
            f"http://{self.device.ip}/Timer",
            data=f'{{ "Value": "TIMER {timer_value} {speed}% DEMAND CONTROL OFF DAY" }}',
        )
        resp.raise_for_status()

    async def _retrieve_status_value(self, field_name: str) -> str:
        status = await self._status()
        if result := re.search(field_name + r" (\S*) ", status):
            return result.group(1)
        raise RuntimeError(f"{field_name} field not found in Qstream status.")

    async def _status(self) -> str:
        return await self._retrieve_value("Status")

    async def _retrieve_value(self, field: str) -> str:
        resp = await self.client_session.get(f"http://{self.device.ip}/{field}")
        resp.raise_for_status()
        resp_json: dict[str, str] = await resp.json()
        return resp_json["Value"]
