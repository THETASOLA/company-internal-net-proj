#!/bin/bash

# Install Postfix
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y postfix mailutils

# Create a test user
useradd -m smtp_test_user

cat << EOF > /etc/postfix/main.cf
# See /usr/share/postfix/main.cf.dist for a commented, more complete version

smtpd_banner = \$myhostname ESMTP \$mail_name
biff = no
append_dot_mydomain = no
readme_directory = no

# Basic configuration
myhostname = smtp.lille.local
mydomain = lille.local
myorigin = \$mydomain
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain, smtp_test_user
relayhost =
mynetworks = 127.0.0.0/8, 192.168.0.0/16
mailbox_size_limit = 0
recipient_delimiter = +
inet_interfaces = all
inet_protocols = all

# TLS parameters
smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
smtpd_use_tls=yes
smtpd_tls_session_cache_database = btree:\${data_directory}/smtpd_scache
smtp_tls_session_cache_database = btree:\${data_directory}/smtp_scache
EOF

systemctl restart postfix

# Ensure mail directory exists for the test user
mkdir -p /home/smtp_test_user/Maildir
chown -R smtp_test_user:smtp_test_user /home/smtp_test_user/Maildir