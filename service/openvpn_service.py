"""Generate server configuration, signal restarts, and read VPN routing status."""

import csv
import re
import time

from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from dto import BaseResponse
from dto.obtain_connected_client import ObtainConnectedClientResponse
from enumeration.openvpn_mode_enums import OpenVPNModeEnums
from enumeration.response_code_enums import ResponseCodeEnums
from util import (network_util,
                  path_util)


def create_openvpn_configuration(mode: OpenVPNModeEnums = OpenVPNModeEnums.FULL_TUNNEL):
    """Write the UDP/1194 server configuration to ``openvpn.conf``.

    Includes PKI paths, TLS settings, configured DNS servers, and either a
    default-gateway push or explicit resource routes. Paths in the generated
    configuration are relative to the shared data directory. File creation
    failures are not checked.

    :param mode: Routing mode; defaults to full tunnel.
    :raises ValueError: If a configured prefix length cannot be converted to an
        integer or produces a negative bit shift.
    """
    log.info(f"Generating openvpn configuration in {mode.mode} mode")
    config = f"""port 1194
proto udp
dev tun

topology subnet
server {env.openvpn_server_network_address} {network_util.bit_number_to_string_network_mask(int(env.openvpn_server_network_mask))}

ca openvpn-pki/certs/ca.crt
cert openvpn-pki/certs/server.crt
key openvpn-pki/private/server.key
crl-verify openvpn-pki/crl/ca.crl

# Usa ECDH fornito da OpenSSL: non richiede dh.pem.
dh none

tls-crypt openvpn-pki/private/ta.key
tls-version-min 1.2

data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305
data-ciphers-fallback AES-256-GCM
auth SHA256
"""
    if mode is OpenVPNModeEnums.FULL_TUNNEL:
        config += """
# Inoltra tutto il traffico Internet del client nel tunnel.
push "redirect-gateway def1 bypass-dhcp"
"""
    else:
        config += "\n# Rete aziendale raggiungibile tramite VPN\n"
        for address, mask in env.openvpn_server_resource_only_routes:
            config += f'push "route {address} {network_util.bit_number_to_string_network_mask(int(mask))}"\n'
    if env.openvpn_server_dns_addresses:
        config += "\n# DNS per i client\n"
        for dns in env.openvpn_server_dns_addresses:
            config += f'push "dhcp-option DNS {dns}"\n'
    config += """
keepalive 10 120
persist-key
persist-tun

user nobody
group nogroup

status openvpn-log/status-server.log
verb 3
explicit-exit-notify 1
"""
    path_util.secure_create_file(file_path=f"{env.openvpn_conf_path}openvpn.conf", data=config)


def create_need_to_restart_file():
    """Write the current epoch milliseconds to the restart signal file.

    The container entrypoint watches the modification time of
    ``openvpn-conf/need_to_restart``. Rewriting it requests a restart; file
    creation failures are not checked.
    """
    log.info("Creating need_to_restart file to signal that openvpn service needs to be restarted")
    current_timestamp = str(int(time.time() * 1000))
    path_util.secure_create_file(file_path=env.openvpn_conf_path + "need_to_restart",
                                 data=current_timestamp)


def obtain_connected_clients() -> BaseResponse:
    """Parse routing entries from the OpenVPN CSV status log.

    Extracts the section between ``ROUTING TABLE`` and ``GLOBAL STATS`` and
    normalizes column names to lowercase with spaces replaced by underscores.

    :return: ``ObtainConnectedClientResponse`` containing routing dictionaries,
        or ``BaseResponse`` with ``REQUESTED_FILE_NOT_FOUND`` if the log is absent.
    :raises OSError: If an existing status log cannot be read.
    :raises AttributeError: If the log lacks the expected routing-table section.
    """
    if not path_util.check_if_file_exists(file_path=env.openvpn_log_path + "status-server.log"):
        return BaseResponse.from_code(ResponseCodeEnums.REQUESTED_FILE_NOT_FOUND)
    status_file_content = path_util.read_file(file_path=env.openvpn_log_path + "status-server.log")
    pattern = re.compile(r"ROUTING\sTABLE\n((.*\n)+)GLOBAL\sSTATS")
    raw_csv = pattern.search(status_file_content).group(1).splitlines()
    parsed_csv = csv.DictReader(raw_csv)
    dictionary = list(parsed_csv)
    for i in range(len(dictionary)):
        dictionary[i] = {k.lower().replace(" ", "_"): v for k, v in dictionary[i].items()}
    return ObtainConnectedClientResponse(code=ResponseCodeEnums.SUCCESS.code,
                                         message=ResponseCodeEnums.SUCCESS.message,
                                         connected_clients=dictionary)
