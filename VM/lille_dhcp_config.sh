#!/bin/bash

apt-get update
apt-get install -y isc-dhcp-server

# Configure
cat << EOF > /etc/dhcp/dhcpd.conf
default-lease-time 600;
max-lease-time 7200;

subnet 192.168.20.0 netmask 255.255.255.0 {
  range 192.168.20.100 192.168.20.250;
  option routers 192.168.20.254;
  option domain-name-servers 192.168.12.2;
  option domain-name "lille.local";
}

subnet 192.168.50.0 netmask 255.255.255.0 {
  range 192.168.50.100 192.168.50.250;
  option routers 192.168.50.254;
  option domain-name-servers 192.168.12.2;
  option domain-name "lille.local";
}

EOF

sed -i 's/INTERFACESv4=""/INTERFACESv4="eth1 eth2"/' /etc/default/isc-dhcp-server

# Restart
systemctl restart isc-dhcp-server