#!/bin/bash

# Lille Internal Firewall Configuration

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

iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p tcp --dport 53 -j ACCEPT

iptables -A INPUT -p udp --dport 67:68 --sport 67:68 -j ACCEPT

iptables -A INPUT -p tcp --dport 25 -j ACCEPT

# Samba traffic
iptables -A INPUT -p tcp --dport 139 -j ACCEPT
iptables -A INPUT -p tcp --dport 445 -j ACCEPT
iptables -A INPUT -p udp --dport 137:138 -j ACCEPT

iptables -A INPUT -p icmp -j ACCEPT

# Allow forwarding (YES there are no rule, we will fix that later)
iptables -A FORWARD -i enp0s8 -j ACCEPT
iptables -A FORWARD -o enp0s8 -j ACCEPT

iptables -A FORWARD -i enp0s9 -j ACCEPT
iptables -A FORWARD -o enp0s9 -j ACCEPT

iptables -A FORWARD -i enp0s10 -j ACCEPT
iptables -A FORWARD -o enp0s10 -j ACCEPT

iptables -A FORWARD -i enp0s16 -j ACCEPT
iptables -A FORWARD -o enp0s16 -j ACCEPT

iptables -A FORWARD -i enp0s17 -j ACCEPT
iptables -A FORWARD -o enp0s17 -j ACCEPT

iptables -A FORWARD -i enp0s18 -j ACCEPT
iptables -A FORWARD -o enp0s18 -j ACCEPT

# Allow forwarding for established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT