#!/bin/bash

# Rennes External Firewall Configuration

# Clear all existing rules and chains
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

iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

iptables -A INPUT -p icmp -j ACCEPT

# Network Address Translation
iptables -t nat -A POSTROUTING -o enp0s8 -j MASQUERADE

iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

iptables -A FORWARD -i enp0s9 -o enp0s8 -j ACCEPT  # LAN_DMZ to WAN
iptables -A FORWARD -i enp0s10 -o enp0s8 -j ACCEPT  # LAN_DHCP to WAN
iptables -A FORWARD -i enp0s16 -o enp0s8 -j ACCEPT  # LAN_INT to WAN

iptables -A FORWARD -i enp0s9 -o enp0s10 -j ACCEPT  # LAN_DMZ to LAN_DHCP
iptables -A FORWARD -i enp0s10 -o enp0s9 -j ACCEPT  # LAN_DHCP to LAN_DMZ
iptables -A FORWARD -i enp0s9 -o enp0s16 -j ACCEPT  # LAN_DMZ to LAN_INT
iptables -A FORWARD -i enp0s16 -o enp0s9 -j ACCEPT  # LAN_INT to LAN_DMZ
iptables -A FORWARD -i enp0s10 -o enp0s16 -j ACCEPT  # LAN_DHCP to LAN_INT
iptables -A FORWARD -i enp0s16 -o enp0s10 -j ACCEPT  # LAN_INT to LAN_DHCP