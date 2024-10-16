#!/bin/bash

apt-get update
apt-get install -y bind9 bind9utils bind9-doc

# BIND9
cat << EOF > /etc/bind/named.conf.local
zone "lille.local" {
    type master;
    file "/etc/bind/zones/db.lille.local";
};

zone "rennes.local" {
    type master;
    file "/etc/bind/zones/db.rennes.local";
};

zone "10.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.10";
};

zone "11.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.11";
};

zone "12.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.12";
};

zone "13.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.13";
};

zone "14.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.14";
};

zone "20.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.20";
};

zone "32.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.32";
};
EOF

# Zones directory
mkdir -p /etc/bind/zones

# Zone files
cat << EOF > /etc/bind/zones/db.lille.local
\$TTL    604800
@       IN      SOA     ns1.lille.local. admin.lille.local. (
                              2         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      ns1.lille.local.
ns1     IN      A       192.168.12.2
firewall-externe   IN      A       192.168.10.1
vpn     IN      A       192.168.10.2
firewall-interne   IN      A       192.168.11.1
dns     IN      A       192.168.12.2
smtp    IN      A       192.168.13.2
nas     IN      A       192.168.14.2
dhcp    IN      A       192.168.20.2
EOF

cat << EOF > /etc/bind/zones/db.rennes.local
\$TTL    604800
@       IN      SOA     ns1.lille.local. admin.lille.local. (
                              2         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      ns1.lille.local.
firewall-externe   IN      A       192.168.10.1
dhcp    IN      A       192.168.11.2
EOF

# Create reverse zone files (only showing one example, repeat for other subnets)
cat << EOF > /etc/bind/zones/db.192.168.10
\$TTL    604800
@       IN      SOA     ns1.lille.local. admin.lille.local. (
                              2         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      ns1.lille.local.
1       IN      PTR     firewall-externe.lille.local.
2       IN      PTR     vpn.lille.local.
EOF

# Create similar reverse zone files for other subnets (192.168.11, 192.168.12, etc.)

# Configure BIND9 options
cat << EOF > /etc/bind/named.conf.options
options {
    directory "/var/cache/bind";
    recursion yes;
    allow-recursion { 192.168.0.0/16; };
    listen-on { 192.168.12.2; };
    allow-transfer { none; };

    forwarders {
        8.8.8.8;
        8.8.4.4;
    };
    
    dnssec-validation auto;
};
EOF

# Restart
systemctl restart bind9