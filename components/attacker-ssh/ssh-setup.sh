#!/bin/bash
# entrypoint.sh



mkdir /run/sshd
useradd -m -s /bin/bash ctf                
echo "ctf:yourpassword" | chpasswd
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config &&
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

/usr/sbin/sshd -D