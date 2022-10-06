import exoscale
import uuid
print("Script starts !")
exo = exoscale.Exoscale()
print("Retrieving zone...")
zone_gva2 = exo.compute.get_zone("ch-gva-2")
print("Retrieving template-back...")
template_back = exo.compute.get_instance_template(zone_gva2, "d7829af2-79bc-43e5-a7be-9e6d6c717553")
print("Retrieving template-front...")
template_front = exo.compute.get_instance_template(zone_gva2, "a70f69fb-10b2-4f6e-aae5-ba26384b62ff")
print("Retrieving security-groups...")
security_group_web = list(exo.compute.list_security_groups())
sg80 = exo.compute.get_security_group(name="default")

print(list(exo.compute.list_instances(zone_gva2)))

print("Creating back instance...")
instance_back = exo.compute.create_instance(
    name="back-" + uuid.uuid4().hex[:10],
    zone=zone_gva2,
    type=exo.compute.get_instance_type("small"),
    template=template_back,
    volume_size=10,
    security_groups=security_group_web,
    user_data=f"""#! /bin/bash
cd /tmp
git clone https://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@github.com/EricB2A/TSM_CloudSys_back_pw1.git
cd TSM_CloudSys_back_pw1
git stash
git fetch --all
git checkout exoscale
git pull
/home/ubuntu/.rbenv/shims/bundle install
RAILS_ENV=production /home/ubuntu/.rbenv/shims/bundle exec rake db:create db:migrate db:seed
/home/ubuntu/.rbenv/shims/rails s -e production -d
"""
 )
print("Creating front instance...")
exo.compute.create_instance(
    name="front-" + uuid.uuid4().hex[:10],
    zone=zone_gva2,
    type=exo.compute.get_instance_type("small"),
    template=template_front,
    volume_size=10,
    security_groups=[sg80],
    user_data=f"""#!/bin/bash
mkdir /tmp/git
cd /tmp/git
git clone https://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@github.com/alex-mottier/TSM_CloudSys_front_pw1.git
cd TSM_CloudSys_front_pw1
rm .env
touch .env
echo "VITE_BACKEND_URL=http://{ instance_back.ipv4_address }:3000" > .env
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
 )
print("VMs are up !")

