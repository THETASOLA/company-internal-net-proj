#!/bin/bash

# Lille Internal Firewall Configuration

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

# Allow incoming DNS queries (UDP port 53 and TCP port 53)
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

# Allow DHCP traffic
iptables -A INPUT -p udp --dport 67:68 --sport 67:68 -j ACCEPT

# Allow incoming SMTP traffic (port 25)
iptables -A INPUT -p tcp --dport 25 -j ACCEPT

# Allow Samba traffic for NAS
iptables -A INPUT -p tcp --dport 139 -j ACCEPT
iptables -A INPUT -p tcp --dport 445 -j ACCEPT
iptables -A INPUT -p udp --dport 137:138 -j ACCEPT

# Allow incoming ICMP (ping) traffic
iptables -A INPUT -p icmp -j ACCEPT

# Allow forwarding between internal networks
# Assuming:
# eth1, eth2, eth3 are for various internal networks
# eth6 is for the new LAN_INT network
iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth3 -j ACCEPT
iptables -A FORWARD -i eth3 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth2 -o eth3 -j ACCEPT
iptables -A FORWARD -i eth3 -o eth2 -j ACCEPT
iptables -A FORWARD -i eth6 -j ACCEPT
iptables -A FORWARD -o eth6 -j ACCEPT

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT