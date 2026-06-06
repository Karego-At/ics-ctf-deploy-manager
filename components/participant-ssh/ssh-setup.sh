#!/bin/bash
# entrypoint.sh



# mkdir /run/sshd
# useradd -m -s /bin/bash ctf                
# echo "ctf:yourpassword" | chpasswd
# sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config &&
# sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# /usr/sbin/sshd -D




# mkdir /run/sshd

# mkdir /run/sshd

# if [ -f /ws/users-setup.json ]; then
#     echo "Found users-setup.json"
#     jq -c '.[]' /ws/users-setup.json
#     while IFS= read -r line; do
#         uname=$(echo "$line" | jq -r '.name')
#         password=$(echo "$line" | jq -r '.password')
#         echo "Creating user: $uname"
#         useradd -m -s /bin/bash "$unamf8182ad700e8e"
#         echo "useradd exit code: $?"
#         echo "$uname:$password" | chpasswd
#         echo "chpasswd exit code: $?"
#     done < <(jq -c '.[]' /ws/users-setup.json)
# else
#     echo "users-setup.json NOT found"
# fi

# sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
# sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
# /usr/sbin/sshd -D





#!/bin/bash
# entrypoint.sh
 
set -e
 
USERS_JSON="/ws/users-setup.json"
 
if [ ! -f "$USERS_JSON" ]; then
  echo "[ERROR] File not found: $USERS_JSON"
  exit 1
fi
 
mkdir -p /run/sshd
 
sed -i 's/#\?PermitRootLogin.*/PermitRootLogin no/'            /etc/ssh/sshd_config
sed -i 's/#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
 
jq -r '.users[] | "\(.name):\(.password)"' "$USERS_JSON" | while IFS=: read -r name password; do
 
  if [ -z "$name" ]; then
    echo "[WARN] Empty name, skipping."
    continue
  fi
 
  if [ -z "$password" ]; then
    echo "[WARN] Empty password for '$name', skipping."
    continue
  fi
 
  if ! id "$name" &>/dev/null; then
    useradd -m -s /bin/bash "$name"
    echo "[OK] Created user: $name"
  else
    echo "[INFO] User exists, updating password: $name"
  fi
 
  echo "${name}:${password}" | chpasswd
  echo "[OK] Password set for: $name"
 
done
 

rm -rf /ws
echo "[INFO] Removed /ws"



echo "[INFO] Starting sshd..."
exec /usr/sbin/sshd -D