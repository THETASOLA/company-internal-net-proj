#!/bin/bash

# Lille External Firewall Configuration

# Clear
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -A INPUT -p tcp --dport 22 -j ACCEPT

iptables -A INPUT -p udp --dport 1194 -j ACCEPT

iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

iptables -A INPUT -p icmp -j ACCEPT

# NAT configuration
iptables -t nat -A POSTROUTING -o enp0s8 -j MASQUERADE

# Forward VPN traffic
iptables -A FORWARD -i enp0s8 -o enp0s9 -p udp --dport 1194 -d 192.168.10.2 -j ACCEPT

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT