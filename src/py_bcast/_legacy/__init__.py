"""Legacy backend protocol modules for py_bcast — not part of the public API.

Houses the AE Broadcast *Legacy* terminal (``bcsys32.exe``) transport stack:
DDE, the AETP binary protocol, ContentProxy HTTP, and the Legacy-specific
parsing/output helpers. The Broadcast+ backend (``_plus/``) never imports from
here; backend-agnostic infrastructure lives in ``_core/``.
"""
