import os
import re

from flask.cli import load_dotenv

from configuration.logging_configuration import logger as __log
from enumeration.openvpn_mode_enums import OpenVPNModeEnums

load_dotenv()

project_base_path = os.path.dirname(os.path.abspath(__file__))
project_base_path = project_base_path.replace("/configuration", "")

openvpn_pki_path = project_base_path + "/target/openvpn-pki/"
openvpn_conf_path = project_base_path + "/target/openvpn-conf/"
openvpn_log_path = project_base_path + "/target/openvpn-log/"
openvpn_rules_path = project_base_path + "/target/openvpn-rules/"

private_keys_path = project_base_path + "/target/openvpn-pki/private/"
certificates_path = project_base_path + "/target/openvpn-pki/certs/"
new_certificates_path = project_base_path + "/target/openvpn-pki/newcerts/"
certificate_revocation_list_path = project_base_path + "/target/openvpn-pki/crl/"
certificate_sign_request_path = project_base_path + "/target/openvpn-pki/csr/"

# Certification Authority
certification_authority_country = os.getenv("CERTIFICATION_AUTHORITY_COUNTRY",
                                            "IT")
certification_authority_organization = os.getenv("CERTIFICATION_AUTHORITY_ORGANIZATION",
                                                 "MiaOrganizzazione")
certification_authority_organization_unit = os.getenv("CERTIFICATION_AUTHORITY_ORGANIZATION_UNIT",
                                                      certification_authority_organization + "-VPN")
certification_authority_common_name = os.getenv("CERTIFICATION_AUTHORITY_COMMON_NAME",
                                                certification_authority_organization + "-VPN-CA")

# Server
server_country = os.getenv("SERVER_COUNTRY",
                           certification_authority_country)
server_organization = os.getenv("SERVER_ORGANIZATION",
                                certification_authority_organization)
server_organization_unit = os.getenv("SERVER_ORGANIZATION_UNIT",
                                     certification_authority_organization_unit)
server_common_name = os.getenv("SERVER_COMMON_NAME",
                               "server")

# OpenVPN Server
openvpn_server_hostname = os.getenv("OPENVPN_SERVER_HOSTNAME")
openvpn_server_network_address = os.getenv("OPENVPN_SERVER_NETWORK_ADDRESS",
                                           "172.27.224.0")
openvpn_server_network_mask = os.getenv("OPENVPN_SERVER_NETWORK_MASK",
                                        "20")
openvpn_server_network_mode = OpenVPNModeEnums.get_by_mode(os.getenv("OPENVPN_SERVER_NETWORK_MODE",
                                                                     "PASSTHROUGH").lower())

__openvpn_server_resource_only_routes_pattern = re.compile(
    r"^OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_(\d+)_(NETWORK_ADDRESS|NETWORK_MASK)$")
__raw_openvpn_server_resource_only_routes = {
    name: value
    for name, value in os.environ.items()
    if __openvpn_server_resource_only_routes_pattern.fullmatch(name)
}
__openvpn_server_resource_only_routes_indexes = []
for name in __raw_openvpn_server_resource_only_routes:
    match = __openvpn_server_resource_only_routes_pattern.search(name)
    __openvpn_server_resource_only_routes_indexes.append(match.group(1))
__openvpn_server_resource_only_routes_valid_indexes = [
    index for index in __openvpn_server_resource_only_routes_indexes if __raw_openvpn_server_resource_only_routes.get(
        f"OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_{index}_NETWORK_ADDRESS") is not None and
                                                                        __raw_openvpn_server_resource_only_routes.get(
                                                                            f"OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_{index}_NETWORK_MASK") is not None
]
__openvpn_server_resource_only_routes_valid_indexes = set(__openvpn_server_resource_only_routes_valid_indexes)

openvpn_server_resource_only_routes = [
    (__raw_openvpn_server_resource_only_routes.get(
        f"OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_{index}_NETWORK_ADDRESS"),
     __raw_openvpn_server_resource_only_routes.get(
         f"OPENVPN_SERVER_RESOURCE_ONLY_ROUTES_{index}_NETWORK_MASK")
    )
    for index in __openvpn_server_resource_only_routes_valid_indexes
]

__openvpn_server_dns_addresses_pattern = re.compile(r"^OPENVPN_SERVER_DNS_(\d+)_ADDRESS$")
__raw_openvpn_server_dns_addresses = {
    name: value
    for name, value in os.environ.items()
    if __openvpn_server_dns_addresses_pattern.fullmatch(name)
}
__openvpn_server_dns_addresses_indexes = []
for name in __raw_openvpn_server_dns_addresses:
    match = __openvpn_server_dns_addresses_pattern.search(name)
    __openvpn_server_dns_addresses_indexes.append(match.group(1))
__openvpn_server_dns_addresses_valid_indexes = [
    index for index in __openvpn_server_dns_addresses_indexes if __raw_openvpn_server_dns_addresses.get(
        f"OPENVPN_SERVER_DNS_{index}_ADDRESS") is not None
]
__openvpn_server_dns_addresses_valid_indexes = set(__openvpn_server_dns_addresses_valid_indexes)
openvpn_server_dns_addresses = [
    __raw_openvpn_server_dns_addresses.get(f"OPENVPN_SERVER_DNS_{index}_ADDRESS")
    for index in __openvpn_server_dns_addresses_valid_indexes
]

# Sanification: the public DNS fallback applies only to the full tunnel (passthrough) mode
if len(openvpn_server_dns_addresses) == 0 and openvpn_server_network_mode == OpenVPNModeEnums.FULL_TUNNEL:
    openvpn_server_dns_addresses = ["8.8.8.8", "8.8.4.4"]

# LOG WARNING
__openvpn_server_resource_only_routes_invalid_indexes = list(
    set(__openvpn_server_resource_only_routes_indexes) ^ set(__openvpn_server_resource_only_routes_valid_indexes)
)
if len(__openvpn_server_resource_only_routes_invalid_indexes) > 0:
    __log.warn(
        f"Indexes without valid network address and mask: {__openvpn_server_resource_only_routes_invalid_indexes}")
