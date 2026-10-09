from enum import Enum, auto


class OpenVPNModeEnums(Enum):
    RESOURCE_ONLY = (auto(), "resource_only")
    FULL_TUNNEL = (auto(), "full_tunnel")

    def __init__(self, code: int,
                 mode: str):
        self.code = code
        self.mode = mode

    @classmethod
    def get_by_mode(cls, mode: str):
        """Return the enum member by its code, or Full Tunnel if not found."""
        for member in cls:
            if member.mode == mode:
                return member
        return OpenVPNModeEnums.FULL_TUNNEL
