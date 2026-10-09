from configuration import environment_configuration as env
from enumeration.openvpn_mode_enums import OpenVPNModeEnums
from util import network_util, path_util


def generate_create_rules_file():
    interface = network_util.get_outgoing_interface()
    if env.openvpn_server_network_mode == OpenVPNModeEnums.FULL_TUNNEL:
        config = f"""iptables -A FORWARD \
-i tun0 -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-j ACCEPT
iptables -A FORWARD \
-i {interface} -o tun0 \
-d {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-m conntrack --ctstate ESTABLISHED,RELATED \
-j ACCEPT
iptables -A POSTROUTING -t nat \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-o {interface} \
-j MASQUERADE"""
    else:
        config = ""
        for address, mask in env.openvpn_server_resource_only_routes:
            config += f"""iptables -A FORWARD -i tun0 -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -d {address}/{mask} -j ACCEPT
iptables -A POSTROUTING -t nat -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -d {address}/{mask} -j MASQUERADE
"""
        config += f"""iptables -A FORWARD -i {interface} -o tun0 \
  -d {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
"""
        config += f"""iptables -A FORWARD -i tun0 -s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -j DROP"""

    path_util.secure_create_file(file_path=f"{env.openvpn_rules_path}iptables.rules.create.bash", data=config)


def generate_delete_rules_file():
    interface = network_util.get_outgoing_interface()
    if env.openvpn_server_network_mode == OpenVPNModeEnums.FULL_TUNNEL:
        config = f"""iptables -D FORWARD \
-i tun0 -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-j ACCEPT
iptables -D FORWARD \
-i {interface} -o tun0 \
-d {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-m conntrack --ctstate ESTABLISHED,RELATED \
-j ACCEPT
iptables -t nat -D POSTROUTING \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
-o {interface} \
-j MASQUERADE"""
    else:
        config = ""
        for address, mask in env.openvpn_server_resource_only_routes:
            config += f"""iptables -D FORWARD -i tun0 -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -d {address}/{mask} -j ACCEPT
iptables -D POSTROUTING -t nat -o {interface} \
-s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -d {address}/{mask} -j MASQUERADE
"""
        config += f"""iptables -D FORWARD -i {interface} -o tun0 \
  -d {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} \
  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
"""
        config += f"""iptables -D FORWARD -i tun0 -s {env.openvpn_server_network_address}/{env.openvpn_server_network_mask} -j DROP"""
    path_util.secure_create_file(file_path=f"{env.openvpn_rules_path}iptables.rules.delete.bash", data=config)
