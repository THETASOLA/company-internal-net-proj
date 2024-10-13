#!/bin/bash

# Install Samba
apt-get update
apt-get install -y samba

# Create a shared directory
mkdir -p /srv/samba/share

# Set permissions
chmod -R 0755 /srv/samba/share
chown -R nobody:nogroup /srv/samba/share

# Configure Samba
cat << EOF > /etc/samba/smb.conf
[global]
   workgroup = WORKGROUP
   server string = Lille NAS
   security = user
   map to guest = bad user
   dns proxy = no

[share]
   path = /srv/samba/share
   browsable = yes
   writable = yes
   guest ok = yes
   read only = no
   create mask = 0755
EOF

# Restart
systemctl restart smbd
systemctl restart nmbd