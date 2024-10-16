#!/bin/bash

apt-get update
apt-get install -y isc-dhcp-server

# Configure
cat << EOF > /etc/dhcp/dhcpd.conf
default-lease-time 600;
max-lease-time 7200;

subnet 192.168.11.0 netmask 255.255.255.0 {
}

subnet 192.168.32.0 netmask 255.255.240.0 {
  range 192.168.32.100 192.168.47.254;
  option routers 192.168.32.1;
  option domain-name-servers 192.168.12.2;  # Using Lille's DNS server
  option domain-name "rennes.local";
}

EOF

sed -i 's/INTERFACESv4=""/INTERFACESv4="eth1"/' /etc/default/isc-dhcp-server

# Restart
systemctl restart isc-dhcp-server