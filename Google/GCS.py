import google.auth
import google.auth.exceptions
import googleapiclient
import googleapiclient.discovery
import re
import sys
import uuid
import warnings
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from typing import Any, List


def create_instance(compute, project, zone, name, image, machine, ip, ip_public, tags=[], metadata=[]):
    config = {
        'name': name,
        'machineType': "zones/%s/machineTypes/%s" % (zone, machine),
        'disks': [
            {
                'initializeParams': {
                    "sourceImage": image
                },
                "boot": True
            }
        ],
        'tags': {
            "items": tags
        },
        "networkInterfaces": [
            {
                'network': 'global/networks/default',
                'networkIP': ip,
                'accessConfigs': [
                    {
                        'type': 'ONE_TO_ONE_NAT',
                        'name': 'External NAT',
                        'natIP': ip_public,
                        'networkTier': 'STANDARD',
                    }
                ]
            }
        ],
        "metadata": {
            "items": metadata
        }
    }
    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()

#########################################
# BACK
#########################################
script_back = f"""#! /bin/bash
cd /tmp
git clone https://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@github.com/EricB2A/TSM_CloudSys_back_pw1.git 2> /tmp/clone
cd TSM_CloudSys_back_pw1
git checkout google > /tmp/checkout_google
/home/amottier/.rbenv/shims/bundle install > /tmp/bundle_install
RAILS_ENV=production /home/amottier/.rbenv/shims/bundle exec rake db:create db:migrate db:seed > /tmp/migrate
/home/amottier/.rbenv/shims/rails s -e production -d  > /tmp/rails_s
"""

BACKEND_IP = '35.216.236.84'
credentials, project_id = google.auth.default()
instance_name_back = "back-" + uuid.uuid4().hex[:10]
instance_zone = "europe-west6-a"
metadata_back = [
    {
        "key": "startup-script",
        "value": script_back
    },
]

compute = googleapiclient.discovery.build('compute', 'v1')
image_back="projects/cloudsys-pw1/global/images/image-back"
create_instance(compute, project_id, instance_zone, instance_name_back, image_back, "e2-micro", "10.172.0.4", BACKEND_IP,
                metadata=metadata_back, tags= ['http-server', 'https-server', 'tcp3000'])

#########################################
# FRONT
#########################################
script_front = f"""#!/bin/bash
mkdir /tmp/git
cd /tmp/git
git clone https://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@github.com/alex-mottier/TSM_CloudSys_front_pw1.git
cd TSM_CloudSys_front_pw1
rm .env
touch .env
echo "VITE_BACKEND_URL=http://{BACKEND_IP}:3000" > .env
curl -sL https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.0/install.sh -o install_nvm.sh 2> /tmp/test0
bash install_nvm.sh 2> /tmp/test1
NVM_DIR="$HOME/.nvm" 2> /tmp/test2
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"  2> /tmp/test3
[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"  2> /tmp/test4
nvm install node --latest 2> /tmp/test5
npm install 2> /tmp/test6
npm run build 2> /tmp/test7
cp -r dist/* /var/www/html
"""
instance_name_front = "front-" + uuid.uuid4().hex[:10]
image_front="projects/cloudsys-pw1/global/images/image-front"
metadata_front = [
    {
        "key": "startup-script",
        "value": script_front
    },
]
FRONTEND_IP="35.216.179.167"
create_instance(compute, project_id, instance_zone, instance_name_front, image_front, "e2-micro", "10.172.0.5", FRONTEND_IP,
                metadata=metadata_front, tags= ['http-server', 'https-server'])
