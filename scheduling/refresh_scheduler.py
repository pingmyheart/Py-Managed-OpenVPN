"""
This scheduler is simply used to refresh certification authority and server certificates and CRL if they are expiring soon.
"""
from util import initialization_util


def refresh_pki():
    initialization_util.refresh()
