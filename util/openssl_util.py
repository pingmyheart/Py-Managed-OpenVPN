def create_openssl_conf_file() -> None:
    """
    Create OpenSSL config file
    """
    from configuration.environment_configuration import (certification_authority_country, \
                                                         certification_authority_organization,
                                                         certification_authority_organization_unit, \
                                                         certification_authority_common_name,
                                                         openvpn_pki_path)
    from util import path_util

    file_data = f'''[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = {openvpn_pki_path}
database          = $dir/index.txt
new_certs_dir     = $dir/newcerts
certificate       = $dir/certs/ca.crt
serial            = $dir/serial
private_key       = $dir/private/ca.key
default_md        = sha256
default_days      = 825
default_crl_days  = 30
crlnumber         = $dir/crlnumber
crl               = $dir/crl/ca.crl
policy            = policy_vpn
unique_subject    = no
copy_extensions   = none

[ policy_vpn ]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = 4096
default_md          = sha256
prompt              = no
distinguished_name  = ca_distinguished_name
x509_extensions     = v3_ca

[ ca_distinguished_name ]
C  = {certification_authority_country}
O  = {certification_authority_organization}
OU = {certification_authority_organization_unit}
CN = {certification_authority_common_name}

[ v3_ca ]
basicConstraints       = critical,CA:true
keyUsage               = critical,keyCertSign,cRLSign
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always,issuer

[ server_cert ]
basicConstraints       = critical,CA:false
keyUsage               = critical,digitalSignature,keyEncipherment
extendedKeyUsage       = serverAuth
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer

[ client_cert ]
basicConstraints       = critical,CA:false
keyUsage               = critical,digitalSignature
extendedKeyUsage       = clientAuth
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer

[ crl_ext ]
authorityKeyIdentifier = keyid:always'''
    path_util.secure_create_file(file_path=openvpn_pki_path + "openssl.cnf", data=file_data)
