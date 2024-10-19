#!/bin/bash

# Lille External Firewall Configuration

# Clear all existing rules and chains
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies: drop all incoming and forwarded traffic, allow all outgoing traffic
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow all traffic on the loopback interface
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow return traffic for established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow incoming SSH connections (port 22)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow incoming VPN connections (OpenVPN uses UDP port 1194 by default)
iptables -A INPUT -p udp --dport 1194 -j ACCEPT

# Allow incoming DNS queries (UDP port 53 and TCP port 53)
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# Allow incoming HTTP and HTTPS traffic (ports 80 and 443)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow incoming ICMP (ping) traffic
iptables -A INPUT -p icmp -j ACCEPT

# Network Address Translation (NAT) configuration
# Assume eth0 is WAN and eth1 is LAN
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Forward VPN traffic to the VPN server (assumed to be at 192.168.10.2)
iptables -A FORWARD -i eth0 -o eth1 -p udp --dport 1194 -d 192.168.10.2 -j ACCEPT

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT