#!/bin/bash

apt-get update
apt-get install -y isc-dhcp-server

# Configure
cat << EOF > /etc/dhcp/dhcpd.conf
default-lease-time 600;
max-lease-time 7200;

subnet 192.168.21.0 netmask 255.255.255.0 {
  range 192.168.21.100 192.168.21.250;
  option routers 192.168.21.254;
  option domain-name-servers 192.168.12.2;  # Using Lille's DNS server
  option domain-name "rennes.local";
}

subnet 192.168.51.0 netmask 255.255.255.0 {
  range 192.168.51.100 192.168.51.250;
  option routers 192.168.51.254;
  option domain-name-servers 192.168.12.2;  # Using Lille's DNS server
  option domain-name "rennes.local";
}

EOF

sed -i 's/INTERFACESv4=""/INTERFACESv4="enp0s8 enp0s9"/' /etc/default/isc-dhcp-server

# Restart
systemctl restart isc-dhcp-server