"""Resolve outgoing interfaces and convert IPv4 prefix lengths to netmasks."""


def get_outgoing_interface(destination: str = "1.1.1.1") -> str:
    """Infer the outgoing interface from a UDP socket's selected source address.

    Connecting the socket selects a route without sending application data.
    Matches its local IPv4 address against interfaces reported by ``psutil``.

    :param destination: IPv4 address or resolvable hostname used for route
        selection; defaults to ``1.1.1.1``.
    :return: Name of the sole interface with the selected source address.
    :raises OSError: If socket creation, name resolution, or route lookup fails.
    :raises RuntimeError: If zero or multiple interfaces match the source address.
    """
    import socket
    import psutil

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        connection.connect((destination, 80))
        source_ip = connection.getsockname()[0]

    interfaces = [
        name
        for name, addresses in psutil.net_if_addrs().items()
        if any(
            address.family == socket.AF_INET and address.address == source_ip
            for address in addresses
        )
    ]

    if len(interfaces) != 1:
        raise RuntimeError(
            f"Cannot uniquely identify the outgoing interface for "
            f"{destination}: source IP={source_ip}, interfaces={interfaces}"
        )

    return interfaces[0]


def bit_number_to_string_network_mask(bit_number: int) -> str:
    """Convert an IPv4 prefix length to a dotted-decimal netmask.

    :param bit_number: Prefix length from 0 to 32, for example ``24``.
    :return: Corresponding netmask, for example ``255.255.255.0``.
    :raises ValueError: If the prefix is outside 0..32 and causes a negative shift.
    """
    mask = (0xffffffff >> (32 - bit_number)) << (32 - bit_number)
    return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
