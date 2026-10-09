from configuration import environment_configuration as env
from configuration.logging_configuration import logger as __log
from util import path_util as __path_util
from util import shell_util as __shell_util


def create_server_private_key() -> None:
    __log.info("Generating server private key")
    __shell_util.run_command(f"""openssl genpkey \
-algorithm RSA \
-pkeyopt rsa_keygen_bits:3072 \
-out {env.private_keys_path}server.key""")
    __path_util.assign_permission_to_file(file_path=env.private_keys_path + "server.key", mode=0o600)


def create_server_certificate() -> None:
    __shell_util.run_command(f"""openssl req -new \
-key {env.private_keys_path}server.key \
-subj '/C={env.server_country}/O={env.server_organization}/OU={env.server_organization_unit}/CN={env.server_common_name}' \
-out {env.certificate_sign_request_path}server.csr""")

    __shell_util.run_command(f"""openssl ca -batch \
-config {env.openvpn_pki_path}openssl.cnf \
-extensions server_cert \
-days 825 \
-notext \
-md sha256 \
-in {env.certificate_sign_request_path}server.csr \
-out {env.certificates_path}server.crt""")
