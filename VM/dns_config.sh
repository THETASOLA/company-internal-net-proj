#!/bin/bash

# Mettre à jour les paquets et installer BIND9
apt-get update
apt-get install -y bind9 bind9utils bind9-doc

# Configuration des zones DNS dans named.conf.local
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

# Créer le répertoire pour les fichiers de zone
mkdir -p /etc/bind/zones

# Fichier de zone pour lille.local
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
firewall-externe   IN      A       192.168.10.254
vpn     IN      A       192.168.10.2
firewall-interne   IN      A       192.168.11.254
dns     IN      A       192.168.12.2
smtp    IN      A       192.168.13.2
nas     IN      A       192.168.14.2
dhcp    IN      A       192.168.20.2
EOF

# Fichier de zone inversée pour 192.168.10
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
254     IN      PTR     firewall-externe.lille.local.
EOF

# Fichier de zone inversée pour 192.168.32
cat << EOF > /etc/bind/zones/db.192.168.32
\$TTL    604800
@       IN      SOA     ns1.lille.local. admin.lille.local. (
                              2         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL
;
@       IN      NS      ns1.lille.local.
1       IN      PTR     some-host.lille.local.
EOF

# Redémarrer le service BIND9
systemctl restart bind9