"""
Internal library for the autopwn scripts.

This library should contain extra code that helps with automatically
pwning CDC boxes.
"""
from .service import detect_service, coerce_service, pwn_service
from .credentials import CredentialBag, Credential
