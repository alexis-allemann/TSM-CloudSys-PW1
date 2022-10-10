import google.auth
import google.auth.exceptions
import googleapiclient
import googleapiclient.discovery
import re
import sys
import uuid
import warnings
import time
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
from typing import Any, List

## export GOOGLE_APPLICATION_CREDENTIALS='Google/cloudsys-pw1-4e0730f1e2eb.json'
def create_address(compute, project, zone, name):
    config = {
        "name": name,
        "networkTier": "STANDARD",
        "region": f"projects/{project}/regions/{zone}"
    }

    return compute.addresses().insert(
        project=project,
        region=zone,
        body=config).execute()

def get_ip_address(compute, project, zone, name):
    address = compute.addresses().get(
        project=project,
        region=zone,
        address=name).execute()

    while(len(address) <= 10):
        address = compute.addresses().get(
            project=project,
            region=zone,
            address=name).execute()

    return address["address"]
def create_instance(compute, project, zone, name, image, machine, ip_public, tags=[], metadata=[]):
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
git clone https://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@github.com/EricB2A/TSM_CloudSys_back_pw1.git 
cd TSM_CloudSys_back_pw1
git stash
git fetch --all
git checkout google
git pull
/home/amottier/.rbenv/shims/bundle install 
RAILS_ENV=production /home/amottier/.rbenv/shims/bundle exec rake db:create db:migrate db:seed 
/home/amottier/.rbenv/shims/rails s -e production -d 
"""

credentials, project_id = google.auth.default()
instance_name_back = "back-" + uuid.uuid4().hex[:10]
instance_zone = "europe-west6-a"
address_zone = "europe-west6"
metadata_back = [
    {
        "key": "startup-script",
        "value": script_back
    },
]
print("Connection to Google API")
compute = googleapiclient.discovery.build('compute', 'v1')
image_back="projects/cloudsys-pw1/global/images/image-back"
address_name_back = f"back-address-{uuid.uuid4().hex[:10]}"
print(f"Project : {project_id}")
print(f"Backend address creation : {address_name_back}")
create_address(compute, project_id, address_zone, address_name_back)

print(f"Retrieve backend address IP : {address_name_back}")
address_back = get_ip_address(compute, project_id, address_zone, address_name_back)
print(f"Backend IP Address : {address_back}")

print(f"Backend instance creation : {instance_name_back}")
create_instance(compute, project_id, instance_zone, instance_name_back, image_back, "e2-micro", address_back,
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
echo "VITE_BACKEND_URL=http://{address_back}:3000" > .env
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
address_name_front = f"front-address-{uuid.uuid4().hex[:10]}"
print(f"Frontend address creation : {address_name_front}")
create_address(compute, project_id, address_zone, address_name_front)

print(f"Retrieve frontend address IP : {address_name_front}")
address_front = get_ip_address(compute, project_id, address_zone, address_name_front)
print(f"Frontend IP Address : {address_front}")

print(f"Frontend instance creation : {instance_name_front}")
create_instance(compute, project_id, instance_zone, instance_name_front, image_front, "e2-micro", address_front,
                metadata=metadata_front, tags= ['http-server', 'https-server'])
print("please wait a few minutes before accessing the frontend, at the following address", address_front)
