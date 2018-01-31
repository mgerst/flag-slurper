"""
Internal library for the autopwn scripts.

This library should contain extra code that helps with automatically
pwning CDC boxes.
"""
from . import exploit
from .credentials import CredentialBag, Credential, credential_bag, flag_bag
from .service import detect_service, coerce_service, pwn_service, Service
