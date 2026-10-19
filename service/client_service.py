"""Manage client PKI assets and produce embedded OpenVPN profiles.

OpenSSL commands run through the shell helper; their nonzero exit codes are not
converted into service errors. Success responses therefore do not guarantee
that all requested PKI changes were completed.
"""

import base64

from cryptography.hazmat._oid import NameOID

from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from dto import BaseResponse
from dto.create_client import CreateClientRequest, CreateClientResponse
from dto.delete_client import DeleteClientRequest
from dto.generate_client_openvpn_file import GenerateClientOpenvpnFileResponse
from dto.renew_client import RenewClientRequest
from dto.revoke_client import RevokeClientRequest
from enumeration.response_code_enums import ResponseCodeEnums
from service import (get_certificate_expiration_in_epoch_millis,
                     actual_timestamp_in_millis, extract_subjects_from_certificate)
from service import openvpn_service
from util import (shell_util,
                  path_util)


def create_client(request_data: CreateClientRequest) -> CreateClientResponse:
    """Generate a client key, CSR, and CA-signed certificate valid for 825 days.

    Uses a 3072-bit RSA key with requested mode 0600 and the configured server
    organization in the subject. An existing private key prevents creation.

    :param request_data: Client name, country, and organizational unit.
    :return: ``BaseResponse`` with ``CLIENT_ALREADY_EXISTS`` if the key exists,
        otherwise ``SUCCESS`` after issuing the commands.
    """
    if path_util.check_if_file_exists(f"{env.private_keys_path}{request_data.client_name}.key"):
        log.info(f"Client '{request_data.client_name}' already exists. Skipping creation.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.CLIENT_ALREADY_EXISTS)

    log.info(f"Creating client '{request_data.client_name}'")
    shell_util.run_command(f"""openssl genpkey \
-algorithm RSA \
-pkeyopt rsa_keygen_bits:3072 \
-out {env.private_keys_path}{request_data.client_name}.key""")
    path_util.assign_permission_to_file(file_path=f"{env.private_keys_path}{request_data.client_name}.key",
                                        mode=0o600)

    shell_util.run_command(f"""openssl req -new \
-key {env.private_keys_path}{request_data.client_name}.key \
-subj '/C={request_data.client_country}/O={env.server_organization}/OU={request_data.client_organization_unit}/CN={request_data.client_name}' \
-out {env.certificate_sign_request_path}{request_data.client_name}.csr""")

    shell_util.run_command(f"""openssl ca -batch \
-config {env.openvpn_pki_path}openssl.cnf \
-extensions client_cert \
-days 825 \
-notext \
-md sha256 \
-in {env.certificate_sign_request_path}{request_data.client_name}.csr \
-out {env.certificates_path}{request_data.client_name}.crt""")
    return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)


def revoke_client(request_data: RevokeClientRequest) -> BaseResponse:
    """Revoke an unexpired client certificate and regenerate the CA CRL.

    Signals a VPN restart after issuing the revocation commands. An expired
    certificate is treated as already unusable and does not trigger a restart.

    :param request_data: Name of the client whose certificate should be revoked.
    :return: ``INTERNAL_ERROR`` if the key or certificate is absent; otherwise a
        ``SUCCESS`` base response.
    :raises OSError: If the certificate exists but cannot be read.
    :raises ValueError: If the certificate cannot be parsed.
    """
    # Check conditions
    if not path_util.check_if_file_exists(f"{env.private_keys_path}{request_data.client_name}.key"):
        log.info(f"Client '{request_data.client_name}' private key does not exist. Cannot revoke.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)
    if not path_util.check_if_file_exists(f"{env.certificates_path}{request_data.client_name}.crt"):
        log.info(f"Client '{request_data.client_name}' certificate does not exist. Cannot revoke.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)

    # Revoke
    if (get_certificate_expiration_in_epoch_millis(
            f"{env.certificates_path}{request_data.client_name}.crt") - actual_timestamp_in_millis()) < 0:
        log.info(f"Client '{request_data.client_name}' certificate is already expired. Skipping revocation.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)
    shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-revoke {env.certificates_path}{request_data.client_name}.crt \
-crl_reason superseded""")

    shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-gencrl \
-out {env.certificate_revocation_list_path}ca.crl""")

    log.info(f"Client '{request_data.client_name}' has been revoked.")
    openvpn_service.create_need_to_restart_file()
    return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)


def renew_client(request_data: RenewClientRequest) -> BaseResponse:
    """Reissue a client certificate for 825 days using its existing private key.

    Preserves country, organization, and organizational unit from the old
    certificate. If it is still valid, revokes it, regenerates the CRL, and
    signals a restart before requesting the replacement certificate.

    :param request_data: Name of the client whose certificate should be renewed.
    :return: ``INTERNAL_ERROR`` if the key or certificate is absent; otherwise a
        ``SUCCESS`` base response after issuing the renewal commands.
    :raises OSError: If the existing certificate cannot be read.
    :raises ValueError: If the existing certificate cannot be parsed.
    :raises IndexError: If a required subject attribute is missing.
    """
    # Check conditions
    if not path_util.check_if_file_exists(f"{env.private_keys_path}{request_data.client_name}.key"):
        log.info(f"Client '{request_data.client_name}' private key does not exist. Cannot renew.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)
    if not path_util.check_if_file_exists(f"{env.certificates_path}{request_data.client_name}.crt"):
        log.info(f"Client '{request_data.client_name}' certificate does not exist. Cannot renew.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)

    # Revoke previous certificate if not expired
    if (get_certificate_expiration_in_epoch_millis(
            f"{env.certificates_path}{request_data.client_name}.crt") - actual_timestamp_in_millis()) > 0:
        log.info(f"Revoking previous certificate for client '{request_data.client_name}'")
        shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-revoke {env.certificates_path}{request_data.client_name}.crt \
-crl_reason superseded""")

        shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-gencrl \
-out {env.certificate_revocation_list_path}ca.crl""")

        openvpn_service.create_need_to_restart_file()

    # Generate new certificate
    certificate_subjects = extract_subjects_from_certificate(f"{env.certificates_path}{request_data.client_name}.crt")
    client_country = certificate_subjects.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value
    server_organization = certificate_subjects.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
    client_organization_unit = certificate_subjects.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)[0].value

    shell_util.run_command(f"""openssl req -new \
-key {env.private_keys_path}{request_data.client_name}.key \
-subj '/C={client_country}/O={server_organization}/OU={client_organization_unit}/CN={request_data.client_name}' \
-out {env.certificate_sign_request_path}{request_data.client_name}.csr""")

    shell_util.run_command(f"""openssl ca -batch \
-config {env.openvpn_pki_path}openssl.cnf \
-extensions client_cert \
-days 825 \
-notext \
-md sha256 \
-in {env.certificate_sign_request_path}{request_data.client_name}.csr \
-out {env.certificates_path}{request_data.client_name}.crt""")

    log.info(f"Client '{request_data.client_name}' has been renewed.")
    return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)


def delete_client(request_data: DeleteClientRequest) -> BaseResponse:
    """Request revocation, then delete the client's private key and certificate.

    Leaves the CSR, CA database, and archived certificates intact. The result
    from ``revoke_client`` is not checked before deleting existing files.

    :param request_data: Name of the client to remove.
    :return: A ``SUCCESS`` base response, including when both files are absent.
    :raises OSError: If certificate reading or file deletion fails.
    :raises ValueError: If a certificate read for revocation cannot be parsed.
    """
    if (not path_util.check_if_file_exists(f"{env.private_keys_path}{request_data.client_name}.key")
            and not path_util.check_if_file_exists(f"{env.certificates_path}{request_data.client_name}.crt")):
        log.info(f"Client '{request_data.client_name}' does not exist. Skipping deletion.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)
    revoke_client(RevokeClientRequest(client_name=request_data.client_name))
    path_util.delete_file(f"{env.private_keys_path}{request_data.client_name}.key")
    path_util.delete_file(f"{env.certificates_path}{request_data.client_name}.crt")
    return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)


def generate_client_openvpn_file(client_name: str):
    """Build a base64-encoded profile with embedded client credentials.

    Embeds the CA and client certificates, client private key, and shared
    ``tls-crypt`` key. Uses the configured server hostname and UDP port 1194.

    :param client_name: Common name and basename of the client's PKI files.
    :return: ``GenerateClientOpenvpnFileResponse`` with the encoded profile, or
        ``BaseResponse`` with ``INTERNAL_ERROR`` if the client key or certificate
        is absent.
    :raises OSError: If a required credential file cannot be read.
    :raises UnicodeDecodeError: If a credential file cannot be decoded as text.
    """
    # Check conditions
    if not path_util.check_if_file_exists(f"{env.private_keys_path}{client_name}.key"):
        log.info(f"Client '{client_name}' private key does not exist. Cannot generate OpenVPN file.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)
    if not path_util.check_if_file_exists(f"{env.certificates_path}{client_name}.crt"):
        log.info(f"Client '{client_name}' certificate does not exist. Cannot generate OpenVPN file.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.INTERNAL_ERROR)

    ca_certificate = path_util.read_file(file_path=f"{env.certificates_path}ca.crt").strip()
    client_certificate = path_util.read_file(file_path=f"{env.certificates_path}{client_name}.crt").strip()
    client_private_key = path_util.read_file(file_path=f"{env.private_keys_path}{client_name}.key").strip()
    tls_crypt_key = path_util.read_file(file_path=f"{env.private_keys_path}ta.key").strip()

    config_content = f"""client
dev tun
proto udp
remote {env.openvpn_server_hostname} 1194

resolv-retry infinite
nobind

remote-cert-tls server
tls-version-min 1.2

data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305
data-ciphers-fallback AES-256-GCM
auth SHA256

persist-key
persist-tun
verb 3

<ca>
{ca_certificate}
</ca>
<cert>
{client_certificate}
</cert>
<key>
{client_private_key}
</key>
<tls-crypt>
{tls_crypt_key}
</tls-crypt>"""

    # encode in base64 singola linea
    encoded_data = base64.b64encode(config_content.encode("utf-8")).decode("ascii")
    return GenerateClientOpenvpnFileResponse(code=ResponseCodeEnums.SUCCESS.code,
                                             message=ResponseCodeEnums.SUCCESS.message,
                                             file_data=encoded_data)
