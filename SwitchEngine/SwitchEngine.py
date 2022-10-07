import openstack as ops
import base64

conn = ops.connection.from_config()

GITHUB_PAT = "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"
KEY_NAME = "Group11-Switch"
SSH_SECURITY_GROUP = "SSH"

BACKEND_IMAGE = "Group11-Backend"
BACKEND_NAME = "Group11-Backend-Scripted"
BACKEND_SECURITY_GROUP = "BACKEND_3000"

FRONTEND_IMAGE = "Group11-Frontend"
FRONTEND_NAME = "Group11-Frontend-Scripted"
FRONTEND_SECURITY_GROUP = "HTTP/HTTPS"

USER_DATA = f"""#!/bin/bash
cd /tmp
touch test.txt
git clone https://{GITHUB_PAT}@github.com/EricB2A/TSM_CloudSys_back_pw1.git
chmod -R 777 TSM_CloudSys_back_pw1  /tmp/chmod
echo "alias sudo=\'sudo env PATH=$PATH\" >> ~/.bashrc
cd TSM_CloudSys_back_pw1
git stash
git fetch --all
git checkout aws
git pull > /tmp/git_pull
/home/ubuntu/.rbenv/shims/bundle install
RAILS_ENV=production /home/ubuntu/.rbenv/shims/bundle exec rake db:create db:migrate db:seed
/home/ubuntu/.rbenv/shims/rails s -e production -d
"""
message_bytes = USER_DATA.encode('ascii')
USER_DATA_B64 = base64.b64encode(message_bytes)

server = conn.compute.create_server(
    name=BACKEND_NAME,
    image_id=conn.compute.find_image(BACKEND_IMAGE).id,
    key_name=conn.compute.find_keypair(KEY_NAME).name,
    security_groups=[{"name": BACKEND_SECURITY_GROUP},
                     {"name": SSH_SECURITY_GROUP}],
    flavor_id=conn.compute.find_flavor("c1.small").id,
    networks=[{"uuid": conn.network.find_network("private").id}],
    user_data=USER_DATA_B64.decode('utf-8')
)
conn.compute.wait_for_server(server)
BACKEND_IP = conn.add_auto_ip(server, wait=True)

print('Backend IP : {}'.format(BACKEND_IP))

USER_DATA = f"""#!/bin/bash
mkdir /tmp/git
cd /tmp/git
git clone https://{GITHUB_PAT}@github.com/alex-mottier/TSM_CloudSys_front_pw1
cd TSM_CloudSys_front_pw1
rm .env
touch .env
echo "VITE_BACKEND_URL=http://{BACKEND_IP}:3000" > .env
curl -sL https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.0/install.sh -o install_nvm.sh 2> /tmp/test0
bash install_nvm.sh 2> /tmp/test1
NVM_DIR="$HOME/.nvm" 2> /tmp/test2
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  2> /tmp/test3
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  2> /tmp/test4
nvm install node --latest 2> /tmp/test5
npm install 2> /tmp/test6
npm run build 2> /tmp/test7
cp -r dist/* /var/www/html
"""

message_bytes = USER_DATA.encode('ascii')
USER_DATA_B64 = base64.b64encode(message_bytes)

server = conn.compute.create_server(
    name=FRONTEND_NAME,
    image_id=conn.compute.find_image(FRONTEND_IMAGE).id,
    key_name=conn.compute.find_keypair(KEY_NAME).name,
    security_groups=[{"name": FRONTEND_SECURITY_GROUP},
                     {"name": SSH_SECURITY_GROUP}],
    flavor_id=conn.compute.find_flavor("c1.small").id,
    networks=[{"uuid": conn.network.find_network("private").id}],
    user_data=USER_DATA_B64.decode('utf-8')
)
conn.compute.wait_for_server(server)
FRONTEND_IP = conn.add_auto_ip(server, wait=True)
print('You can now connect to http://{}'.format(FRONTEND_IP))