def check_openvpn_is_installed():
    """
    Check if OpenVPN is installed on the system using agnostic approach.
    :return: True if OpenVPN is installed, False otherwise
    """
    import subprocess

    try:
        subprocess.run(["openvpn", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_openssl_is_installed():
    """
    Check if OpenSSL is installed on the system using agnostic approach.
    :return: True if OpenSSL is installed, False otherwise
    """
    import subprocess

    try:
        subprocess.run(["openssl", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
