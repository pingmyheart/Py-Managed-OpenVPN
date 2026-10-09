#!/bin/bash
set -euo pipefail

openvpn_pid=""

function start_openvpn(){
    openvpn --config openvpn-conf/openvpn.conf &
    openvpn_pid=$!
}
function stop_openvpn(){
    if [[ -n "$openvpn_pid" ]] && kill -0 "$openvpn_pid" 2>/dev/null; then
      kill -9 "$openvpn_pid"
      # wait also reaps the child, so the process is really gone when it returns
      wait "$openvpn_pid" 2>/dev/null || true
      echo "OpenVPN process $openvpn_pid terminated."
    fi
    openvpn_pid=""
}
function restart_openvpn(){
  echo "Restart requested. Restarting OpenVPN..."
    stop_openvpn
    start_openvpn
}
function create_iptables_rules(){
  echo "Creating iptables rules..."
  bash openvpn-rules/iptables.rules.create.bash
  echo "iptables rules created."
}
function delete_iptables_rules(){
  echo "Deleting iptables rules..."
  bash openvpn-rules/iptables.rules.delete.bash
  echo "iptables rules deleted."
}

cd /etc/openvpn-custom

if [[ ! -r openvpn-conf/openvpn.conf ]]; then
    echo "OpenVPN configuration is missing or unreadable: openvpn-conf/openvpn.conf" >&2
    exit 1
fi

create_iptables_rules

start_openvpn

trap delete_iptables_rules SIGTERM
trap delete_iptables_rules SIGKILL

file="/etc/openvpn-custom/openvpn-conf/need_to_restart"
last=""

while :; do
    current=$(stat -c %Y "$file" 2>/dev/null)

    if [[ "$current" != "$last" ]]; then
        if [[ -n "$last" ]]; then
            restart_openvpn
        fi
        last="$current"
    fi

    sleep 1
done