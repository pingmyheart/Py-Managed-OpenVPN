"""Define supported VPN routing modes and their configuration values."""

from enum import Enum, auto


class OpenVPNModeEnums(Enum):
    """Select full-tunnel routing or access limited to configured resources.

    :ivar code: Automatically assigned numeric identifier.
    :ivar mode: String value used in environment configuration.
    """
    RESOURCE_ONLY = (auto(), "resource_only")
    FULL_TUNNEL = (auto(), "full_tunnel")

    def __init__(self, code: int,
                 mode: str):
        """Store the routing mode's identifier and configuration value.

        :param code: Numeric identifier assigned to the member.
        :param mode: Configuration string identifying the routing mode.
        """
        self.code = code
        self.mode = mode

    @classmethod
    def get_by_mode(cls, mode: str):
        """Look up a mode by its exact, case-sensitive configuration string.

        :param mode: String to compare with each member's ``mode`` attribute.
        :return: Matching member, or ``FULL_TUNNEL`` when no member matches.
        """
        for member in cls:
            if member.mode == mode:
                return member
        return OpenVPNModeEnums.FULL_TUNNEL
