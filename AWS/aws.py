import boto3 
import sys
if len(sys.argv) != 2:
  print("please provide your PEM key...")
  print("python3 aws.py <path_to_file>")
  exit(1)


# configuration
INSTANCE_TYPE = "t2.micro"
KEY_NAME = sys.argv[1]
print("Your key : ", KEY_NAME)

BACKEND_AMI = "ami-0e7a9e257501dd3da"
BACKEND_NAME = "Group11-Backend-Scripted"
BACKEND_SECURITY_GROUPS = ["launch-wizard-17"]

FRONTEND_AMI = "ami-077213bde25c0784a"
FRONTEND_NAME = "Group11-Frontend-Scripted"
FRONTEND_SECURITY_GROUPS = ["launch-wizard-17"]

# backend script
USER_DATA = f"""#!/bin/bash
cd /tmp
git clone https://github.com/EricB2A/TSM_CloudSys_back_pw1.git
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

ec2 = boto3.resource('ec2')
instances = ec2.create_instances(
    ImageId=BACKEND_AMI,
    MinCount=1,
    MaxCount=1,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEY_NAME,
    SecurityGroups=BACKEND_SECURITY_GROUPS,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': BACKEND_NAME
                },
            ]
        },
    ],
    UserData=USER_DATA
)
instances[0].wait_until_running()
instances[0].reload()
BACKEND_IP = instances[0].public_ip_address

# frontend
USER_DATA = f"""#!/bin/bash
mkdir /tmp/git
cd /tmp/git
git clone https://github.com/alex-mottier/TSM_CloudSys_front_pw1
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

ec2 = boto3.resource('ec2')
ec2.create_instances(
    ImageId=FRONTEND_AMI,
    MinCount=1,
    MaxCount=1,
    InstanceType=INSTANCE_TYPE,
    KeyName=KEY_NAME,
    SecurityGroups=FRONTEND_SECURITY_GROUPS,
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': FRONTEND_NAME
                },
            ]
        },
    ],
    UserData=USER_DATA
)