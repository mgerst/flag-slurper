from typing import Tuple, Dict, Any, Optional, List

from flag_slurper.autolib.post import PostContext
from .exploit import FlagConf
from .models import Service
from .protocols import PWN_FUNCS
from .post import registry

SERVICE_MAP = {
    22: 'ssh',
    25: 'smtp',
    53: 'dns',
    80: 'http',
    443: 'https',
    3389: 'rdp',
}


class Result:
    def __init__(self, service: Service, message: str, *, success: bool, skipped: bool):
        self.service = service
        self.message = message
        self.success = success
        self.skipped = skipped
        self.proto, self.url, self.port = detect_service(service)

    def __eq__(self, other):
        return self.service == other.service \
               and self.message == other.message \
               and self.success == other.success \
               and self.skipped == other.skipped

    def __str__(self):
        header = "{team}/{url}:{port}/{proto}".format(team=self.service.team.number, url=self.url, port=self.port,
                                                      proto=self.proto)
        if not self.success and not self.skipped:
            return "{} Failed pwn: {}".format(header, self.message)
        elif not self.success and self.skipped:
            return "{} Skipped pwn: {}".format(header, self.message)
        elif self.success:
            return "{} Succeeded!  {}".format(header, self.message)

    def __repr__(self):  # pragma: no cover
        return '<Result "{}">'.format(self.__str__())


def coerce_service(service: Dict[str, Any]) -> Service:
    return Service(**service)


def detect_service(service: Service) -> Tuple[str, int, str]:
    if service.service_port not in SERVICE_MAP:
        return 'unknown', service.service_url, service.service_port
    return SERVICE_MAP[service.service_port], service.service_url, service.service_port


def pwn_service(service: Service, flag_conf: Optional[FlagConf], limit_creds: Optional[List[str]],
                config: List[dict]) -> Result:
    registry.configure(config)
    proto, url, port = detect_service(service)
    if proto not in PWN_FUNCS:
        return Result(service=service, message="Protocol not supported for autopwn", success=False, skipped=True)

    context = PostContext()
    message, success, skipped = PWN_FUNCS[proto](url, port, service, flag_conf, limit_creds, context)
    registry.post(service, context)
    return Result(service=service, message=message, success=success, skipped=skipped)
