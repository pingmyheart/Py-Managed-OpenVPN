"""Provide the scheduled job that checks CA, server, and CRL expiration."""
from util import initialization_util


def refresh_pki():
    """Refresh expiring PKI assets and signal a VPN restart after renewal.

    CA and server certificates use a 30-day renewal window; the CRL uses five
    days. File and certificate parsing errors propagate to the scheduler.
    """
    initialization_util.refresh()
