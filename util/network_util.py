def get_outgoing_interface(destination: str = "1.1.1.1") -> str:
    """
    Infer the outgoing interface for an IPv4 destination.
    Raise an error if no unique interface can be identified.
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
    """
    Convert a bit number to a string representation of a network mask.
    For example, 24 -> "255.255.255.0"
    """
    mask = (0xffffffff >> (32 - bit_number)) << (32 - bit_number)
    return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
