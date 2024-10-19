#!/bin/bash

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (adjust if your SSH port is different)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow VPN (OpenVPN)
iptables -A INPUT -p udp --dport 1194 -j ACCEPT

# Allow DNS
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# Allow HTTP and HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow ICMP (ping)
iptables -A INPUT -p icmp -j ACCEPT

# NAT (assuming eth0 is WAN and eth1 is LAN)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Forward VPN traffic to VPN server
iptables -A FORWARD -i eth0 -o eth1 -p udp --dport 1194 -d 192.168.10.2 -j ACCEPT

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4