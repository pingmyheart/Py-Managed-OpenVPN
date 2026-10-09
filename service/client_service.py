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
    if (not path_util.check_if_file_exists(f"{env.private_keys_path}{request_data.client_name}.key")
            and not path_util.check_if_file_exists(f"{env.certificates_path}{request_data.client_name}.crt")):
        log.info(f"Client '{request_data.client_name}' does not exist. Skipping deletion.")
        return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)
    revoke_client(RevokeClientRequest(client_name=request_data.client_name))
    path_util.delete_file(f"{env.private_keys_path}{request_data.client_name}.key")
    path_util.delete_file(f"{env.certificates_path}{request_data.client_name}.crt")
    return BaseResponse.from_code(code_enum=ResponseCodeEnums.SUCCESS)


def generate_client_openvpn_file(client_name: str):
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
