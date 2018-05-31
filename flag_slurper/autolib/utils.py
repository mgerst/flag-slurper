from typing import List

from .exploit import LimitCreds
from .models import CredentialBag


def limited_credentials(limit: LimitCreds) -> List[CredentialBag]:
    """
    Filter the credentials bags by the given usernames.

    :param limit: The usernames to filter
    :return: The filtered list of credential bags
    """
    creds = CredentialBag.select()
    if not limit:
        return creds
    return creds.where(CredentialBag.username.in_(limit))
