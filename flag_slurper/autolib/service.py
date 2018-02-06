from collections import namedtuple
from typing import Tuple, Dict, Any

from .protocols import PWN_FUNCS

SERVICE_MAP = {
    22: 'ssh',
    53: 'dns',
    80: 'http',
    443: 'https',
    3389: 'rdp',
}

Service = namedtuple('Service', ['id', 'service_id', 'service_name', 'service_port', 'service_url', 'team_id',
                                 'team_name', 'team_number', 'admin_status', 'high_target', 'low_target', 'is_rand'])


class Result:
    def __init__(self, service: Service, message: str, *, success: bool, skipped: bool):
        self.service = service
        self.message = message
        self.success = success
        self.skipped = skipped
        self.proto, self.url, self.port = detect_service(service)

    def __str__(self):
        header = "{team}/{url}:{port}/{proto}".format(team=self.service.team_number, url=self.url, port=self.port,
                                                      proto=self.proto)
        if not self.success and not self.skipped:
            return "{} Failed pwn: {}".format(header, self.message)
        elif not self.success and self.skipped:
            return "{} Skipped pwn: {}".format(header, self.message)
        elif self.success:
            return "{} Succeeded!  {}".format(header, self.message)


def coerce_service(service: Dict[str, Any]) -> Service:
    return Service(**service)


def detect_service(service: Service) -> Tuple[str, int, str]:
    if service.service_port not in SERVICE_MAP:
        return 'unknown', service.service_url, service.service_port
    return SERVICE_MAP[service.service_port], service.service_url, service.service_port


def pwn_service(service: Service) -> Result:
    proto, url, port = detect_service(service)
    if proto not in PWN_FUNCS:
        return Result(service=service, message="Protocol not supported for autopwn", success=False, skipped=True)

    message, success, skipped = PWN_FUNCS[proto](url, port, service)
    return Result(service=service, message=message, success=success, skipped=skipped)
