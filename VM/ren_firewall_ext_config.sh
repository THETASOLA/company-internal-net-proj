#!/bin/bash

# Rennes External Firewall Configuration

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

# Allow incoming HTTP and HTTPS traffic (ports 80 and 443)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow incoming ICMP (ping) traffic
iptables -A INPUT -p icmp -j ACCEPT

# Network Address Translation (NAT) configuration
# Assume eth0 is WAN, eth1 is LAN_DMZ, eth2 is LAN_DHCP, and eth3 is LAN_INT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow internal networks to access the internet
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT  # LAN_DMZ to WAN
iptables -A FORWARD -i eth2 -o eth0 -j ACCEPT  # LAN_DHCP to WAN
iptables -A FORWARD -i eth3 -o eth0 -j ACCEPT  # LAN_INT to WAN

# Allow communication between internal networks
iptables -A FORWARD -i eth1 -o eth2 -j ACCEPT  # LAN_DMZ to LAN_DHCP
iptables -A FORWARD -i eth2 -o eth1 -j ACCEPT  # LAN_DHCP to LAN_DMZ
iptables -A FORWARD -i eth1 -o eth3 -j ACCEPT  # LAN_DMZ to LAN_INT
iptables -A FORWARD -i eth3 -o eth1 -j ACCEPT  # LAN_INT to LAN_DMZ
iptables -A FORWARD -i eth2 -o eth3 -j ACCEPT  # LAN_DHCP to LAN_INT
iptables -A FORWARD -i eth3 -o eth2 -j ACCEPT  # LAN_INT to LAN_DHCP