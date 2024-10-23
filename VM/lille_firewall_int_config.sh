#!/bin/bash

# Lille Internal Firewall Configuration

# Clear
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# DMZ/VPN Rules
iptables -A INPUT -s 192.168.11.2 -p tcp --sport 1194 -m multiport --dports 80,443,25,143,993,53 -j ACCEPT
iptables -A INPUT -s 192.168.11.2 -p udp --sport 1194 --dport 53 -j ACCEPT
iptables -A INPUT -s 192.168.11.2 -j LOG --log-prefix "Denied VPN IN: "
iptables -A INPUT -s 192.168.11.2 -j DROP

iptables -A OUTPUT -d 192.168.11.2 -p tcp -m multiport --sports 25,143,993,53 --dport 1194 -j ACCEPT
iptables -A OUTPUT -d 192.168.11.2 -p udp --sport 53 --dport 1194 -j ACCEPT
iptables -A OUTPUT -d 192.168.11.2 -j LOG --log-prefix "Denied VPN OUT: "
iptables -A OUTPUT -d 192.168.11.2 -j DROP

# DNS Rules
iptables -A OUTPUT -s 192.168.12.2 -p udp --sport 53 -j ACCEPT
iptables -A INPUT -d 192.168.12.2 -p udp --dport 53 -j ACCEPT

# DHCP Rules
iptables -A OUTPUT -s 192.168.20.2 -p udp --sport 67:68 -j ACCEPT
iptables -A INPUT -d 192.168.20.2 -p udp --dport 67:68 -j ACCEPT

# SMTP/IMAP Rules
iptables -A OUTPUT -s 192.168.13.2 -p tcp -m multiport --sports 25,143,993 -j ACCEPT
iptables -A INPUT -d 192.168.13.2 -p tcp -m multiport --dports 25,143,993 -j ACCEPT

# Forward rules
iptables -A FORWARD -i enp0s8 -o enp0s9 -m state --state NEW -j ACCEPT
iptables -A FORWARD -i enp0s9 -o enp0s8 -m state --state NEW -j ACCEPT

# Forwarding
iptables -A FORWARD -i enp0s16 -o enp0s10 -p udp --dport 53 -j ACCEPT
iptables -A FORWARD -i enp0s10 -o enp0s16 -p udp --sport 53 -j ACCEPT

iptables -A FORWARD -i enp0s16 -o enp0s17 -p udp --dport 67:68 --sport 67:68 -j ACCEPT
iptables -A FORWARD -i enp0s17 -o enp0s16 -p udp --sport 67:68 --dport 67:68 -j ACCEPT

iptables -A FORWARD -i enp0s16 -o enp0s18 -p tcp --dport 25 -j ACCEPT
iptables -A FORWARD -i enp0s18 -o enp0s16 -p tcp --sport 25 -j ACCEPT

iptables -A FORWARD -i enp0s16 -o enp0s18 -p tcp -m multiport --dports 143,993 -j ACCEPT
iptables -A FORWARD -i enp0s18 -o enp0s16 -p tcp -m multiport --sports 143,993 -j ACCEPT

iptables -A FORWARD -i enp0s16 -o enp0s8 -p tcp -m multiport --dports 80,443 -j ACCEPT
iptables -A FORWARD -i enp0s8 -o enp0s16 -p tcp -m multiport --sports 80,443 -j ACCEPT

# Established connections
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Deny rest
iptables -A INPUT -j LOG --log-prefix "Denied IN: "
iptables -A INPUT -j DROP
iptables -A FORWARD -j LOG --log-prefix "Denied FORWARD: "
iptables -A FORWARD -j DROP
iptables -A OUTPUT -j LOG --log-prefix "Denied OUT: "
iptables -A OUTPUT -j DROP

# Configure DNS resolver (not sure is relevant in a firewall)
cat << EOF > /etc/systemd/resolved.conf
[Resolve]
DNS=192.168.12.2
Domains=lille.local
EOF

# Restart systemd-resolved
systemctl restart systemd-resolved