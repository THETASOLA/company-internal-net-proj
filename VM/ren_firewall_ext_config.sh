#!/bin/bash

# Rennes External Firewall Configuration

# Clear
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Rules
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Web
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# VPN Rules
iptables -A INPUT -p udp --dport 1194 -d 192.168.21.254 -j ACCEPT

iptables -A OUTPUT -p udp --sport 1194 -s 192.168.21.254 -j ACCEPT

iptables -A INPUT -d 192.168.21.254 -j LOG --log-prefix "Denied VPN IN: "
iptables -A INPUT -d 192.168.21.254 -j DROP
iptables -A OUTPUT -s 192.168.21.254 -j LOG --log-prefix "Denied VPN OUT: "
iptables -A OUTPUT -s 192.168.21.254 -j DROP

# Network Address Translation
iptables -t nat -A POSTROUTING -o enp0s8 -j MASQUERADE

# Forward rules for internal networks
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -i enp0s9 -o enp0s8 -j ACCEPT  # LAN_DHCP to WAN
iptables -A FORWARD -i enp0s10 -o enp0s8 -j ACCEPT  # LAN_INT to WAN

iptables -A FORWARD -i enp0s9 -o enp0s10 -j ACCEPT  # LAN_DHCP to LAN_INT
iptables -A FORWARD -i enp0s10 -o enp0s9 -j ACCEPT  # LAN_INT to LAN_DHCP

# Deny rest
iptables -A INPUT -j LOG --log-prefix "Denied IN: "
iptables -A INPUT -j DROP
iptables -A FORWARD -j LOG --log-prefix "Denied FORWARD: "
iptables -A FORWARD -j DROP

# Configure DNS resolver (not sure is relevant in a firewall)
cat << EOF > /etc/systemd/resolved.conf
[Resolve]
DNS=192.168.12.2
Domains=lille.local
EOF

# Restart systemd-resolved
systemctl restart systemd-resolved