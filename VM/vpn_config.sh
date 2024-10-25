#!/bin/bash

# Install OpenVPN and OpenSSL
apt-get update
apt-get install -y openvpn openssl

# Create the directory for the certificates
mkdir -p /etc/openvpn/keys
cd /etc/openvpn/keys

# Set up the Certificate Authority
openssl genrsa -out ca.key 1024
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=MyVPN CA"

# Generate certificate
openssl genrsa -out server.key 1024
openssl req -new -key server.key -out server.csr -subj "/CN=MyVPN Server"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

openssl genrsa -out client.key 1024
openssl req -new -key client.key -out client.csr -subj "/CN=MyVPN Client"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365

openssl dhparam -out dh.pem 1024

openvpn --genkey --secret ta.key

# Configure OpenVPN
cat << EOF > /etc/openvpn/server.conf
port 1194
proto udp
dev tun
ca /etc/openvpn/keys/ca.crt
cert /etc/openvpn/keys/server.crt
key /etc/openvpn/keys/server.key
dh /etc/openvpn/keys/dh.pem
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
push "route 192.168.0.0 255.255.0.0"
keepalive 10 120
tls-auth /etc/openvpn/keys/ta.key 0
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
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o enp0s8 -j MASQUERADE

# Start OpenVPN service
systemctl start openvpn@server
systemctl enable openvpn@server

# Create OpenVPN Client Configuration (we use this for testing, the file would need to be shared with the client)
cat << EOF > /etc/openvpn/client.ovpn
client
dev tun
proto udp
remote 192.168.10.2 1194 # Connect to the VPN server
resolv-retry infinite
nobind
persist-key
persist-tun
auth SHA256
cipher AES-256-CBC
key-direction 1
tls-auth ta.key 1

<ca>
$(cat ca.crt)
</ca>
<cert>
$(cat client.crt)
</cert>
<key>
$(cat client.key)
</key>
EOF

chmod 600 /etc/openvpn/client.ovpn

# Configure DNS resolver
cat << EOF > /etc/systemd/resolved.conf
[Resolve]
DNS=192.168.12.2
Domains=lille.local
EOF

# Restart systemd-resolved
systemctl restart systemd-resolved