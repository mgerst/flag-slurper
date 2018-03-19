"""
Internal library for the autopwn scripts.

This library should contain extra code that helps with automatically
pwning CDC boxes.
"""
from . import exploit
from .models import Service
from .service import detect_service, coerce_service, pwn_service
