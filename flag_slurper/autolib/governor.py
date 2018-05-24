import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


class Governor:
    """
    The governor tracks the number of connections over time
    to a given ip address. This is used for fail2ban evasion.

    This can be configured in the flagrc.

    * ``autopwn->governor`` (default false) whether the governor is enabled.
    * ``autopwn->delay`` (default 5m) how long to wait after limiting.
    * ``autopwn->window`` (default 30m) the window to track attempts in.
    * ``autopwn->times`` (default 3) max attempts inside of the window.
    """
    instance = None

    def __init__(self, enabled: bool, delay: int = 5 * 60, window: int = 30 * 60, times: int = 3):
        self.enabled = enabled
        self.delay = delay
        self.window = window
        self.times = times

        # Dict[IP, timestamp]
        self.limits = defaultdict(list)

    @classmethod
    def get_instance(cls, enabled: Optional[bool] = False, delay: Optional[int] = 5 * 60,
                     window: Optional[int] = 30 * 60, times: Optional[int] = 3) -> 'Governor':
        if not Governor.instance:
            Governor.instance = cls(enabled, delay, window, times)
        return Governor.instance

    def filter(self, ipaddr: str):
        def _filter(x: datetime):
            return x > datetime.now() - timedelta(seconds=self.window)

        self.limits[ipaddr] = list(filter(_filter, self.limits[ipaddr]))

    def attempt(self, ipaddr: str):
        self.filter(ipaddr)
        self.limits[ipaddr].append(datetime.now())
        if len(self.limits[ipaddr]) > self.times:
            time.sleep(self.delay)
