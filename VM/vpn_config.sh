#!/bin/bash

# Install OpenVPN
apt-get update
apt-get install -y openvpn easy-rsa

# Set up the PKI
make-cadir /etc/openvpn/easy-rsa
cd /etc/openvpn/easy-rsa

# Initialize the PKI
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa gen-dh
openvpn --genkey --secret /etc/openvpn/ta.key

# Generate server certificate
./easyrsa gen-req server nopass
./easyrsa sign-req server server

# Generate client certificate
./easyrsa gen-req client nopass
./easyrsa sign-req client client

# Configure OpenVPN server
cat << EOF > /etc/openvpn/server.conf
port 1194
proto udp
dev tun
ca /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/server.crt
key /etc/openvpn/easy-rsa/pki/private/server.key
dh /etc/openvpn/easy-rsa/pki/dh.pem
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "route 192.168.0.0 255.255.0.0"
keepalive 10 120
tls-auth /etc/openvpn/ta.key 0
cipher AES-256-CBC
compress lz4-v2
push "compress lz4-v2"
max-clients 100
user nobody
group nogroup
persist-key
persist-tun
status openvpn-status.log
verb 3
EOF

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Configure NAT
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
echo "iptables-persistent iptables-persistent/autosave_v4 boolean true" | debconf-set-selections
echo "iptables-persistent iptables-persistent/autosave_v6 boolean true" | debconf-set-selections
apt-get install -y iptables-persistent

# Start OpenVPN service
systemctl start openvpn@server
systemctl enable openvpn@server