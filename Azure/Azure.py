# Import the needed credential and management objects from the libraries.

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
import os
import base64
from dotenv import load_dotenv

load_dotenv()

print(f"\nProvisioning backend... some operations might take a minute or two.")

# Acquire a credential object using CLI-based authentication.
credential = DefaultAzureCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

# Step 1: Provision a resource group

# Obtain the management object for resources, using the credentials from the CLI login.
resource_client = ResourceManagementClient(credential, subscription_id)

# Constants we need in multiple places: the resource group name and the region
# in which we provision resources. You can change these values however you want.
RESOURCE_GROUP_NAME = "Cloud-PW1"
LOCATION = "westeurope"

# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME,
    {
        "location": LOCATION
    }
)


# For details on the previous code, see Example: Provision a resource group
# at https://docs.microsoft.com/azure/developer/python/azure-sdk-example-resource-group


# Step 2: provision a virtual network

# A virtual machine requires a network interface client (NIC). A NIC requires
# a virtual network and subnet along with an IP address. Therefore we must provision
# these downstream components first, then provision the NIC, after which we
# can provision the VM.

# Network and IP address names
VNET_NAME = "cloud-back-vnet"
SUBNET_NAME = "cloud-back-subnet"
IP_NAME = "cloud-back-ip"
IP_CONFIG_NAME = "cloud-back-ip-config"
NIC_NAME = "cloud-back-nic"

# Obtain the management object for networks
network_client = NetworkManagementClient(credential, subscription_id)

# Provision the virtual network and wait for completion
poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {
            "address_prefixes": ["10.0.0.0/16"]
        }
    }
)

vnet_result = poller.result()

# Step 3: Provision the subnet and wait for completion
poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, 
    VNET_NAME, SUBNET_NAME,
    { "address_prefix": "10.0.0.0/24" }
)
subnet_result = poller.result()

# Step 4: Provision an IP address and wait for completion
poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

backend_address = poller.result()

print(f"Provisioned public IP address {backend_address.name} with address {backend_address.ip_address}")
backend_ip_adress = backend_address.ip_address

# Step 5: Provision the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": subnet_result.id },
            "public_ip_address": {"id": backend_address.id }
        }],
        "networkSecurityGroup": {
            "id": "/subscriptions/2cd750f4-c1b1-4718-a900-5391f32ef071/resourcegroups/Cloud/providers/Microsoft.Network/networkSecurityGroups/cloud-nsg"
        }
    }
)

nic_result = poller.result()

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

VM_NAME = "cloud-back"
USERNAME = "cloud-back"
PASSWORD = "Cloud-system2"

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "properties": {
            "hardwareProfile": {
                "vmSize": "Standard_D2s_v3"
            },
            "storageProfile": {
                "imageReference": {
                    "id": "/subscriptions/2cd750f4-c1b1-4718-a900-5391f32ef071/resourceGroups/Cloud/providers/Microsoft.Compute/images/cloud-back-image-20221002163937"
                },                           
                "osDisk": {
                    "caching": "ReadWrite",
                    "managedDisk": {
                        "storageAccountType": "Premium_LRS"
                    },
                    "name": "cloud-back-disk",
                    "createOption": "FromImage"
                }
            },
            "osProfile": {
                "computer_name": VM_NAME,
                "admin_username": USERNAME,
                "admin_password": PASSWORD
            },
            "networkProfile": {
                "networkInterfaces": [
                {
                    "id": nic_result.id,
                    "properties": {
                        "primary": True
                    }
                }]
            },
            "userData": str(base64.b64encode(bytes('#!/bin/bash\ncd /tmp\ngit clone https://'+ str(os.environ["GITHUB_PAT"]) +'@github.com/EricB2A/TSM_CloudSys_back_pw1.git 2> /tmp/clone\ncd TSM_CloudSys_back_pw1\n/home/cloud-back/.rbenv/shims/bundle install > /tmp/bundle_install\nRAILS_ENV=production /home/cloud-back/.rbenv/shims/bundle exec rake db:create db:migrate db:seed > /tmp/migrate\n/home/cloud-back/.rbenv/shims/rails s -e production -d  > /tmp/rails_s\n', 'utf-8')))[2:-1]
        }                                                                      
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")

print(f"\nProvisioning frontend... some operations might take a minute or two.")

# Acquire a credential object using CLI-based authentication.
credential = DefaultAzureCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

# Step 1: Provision a resource group

# Obtain the management object for resources, using the credentials from the CLI login.
resource_client = ResourceManagementClient(credential, subscription_id)

# Constants we need in multiple places: the resource group name and the region
# in which we provision resources. You can change these values however you want.
RESOURCE_GROUP_NAME = "Cloud-PW1"
LOCATION = "westeurope"

# Provision the resource group.
rg_result = resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME,
    {
        "location": LOCATION
    }
)

# For details on the previous code, see Example: Provision a resource group
# at https://docs.microsoft.com/azure/developer/python/azure-sdk-example-resource-group


# Step 2: provision a virtual network

# A virtual machine requires a network interface client (NIC). A NIC requires
# a virtual network and subnet along with an IP address. Therefore we must provision
# these downstream components first, then provision the NIC, after which we
# can provision the VM.

# Network and IP address names
VNET_NAME = "cloud-front-vnet"
SUBNET_NAME = "cloud-front-subnet"
IP_NAME = "cloud-front-ip"
IP_CONFIG_NAME = "cloud-front-ip-config"
NIC_NAME = "cloud-front-nic"

# Obtain the management object for networks
network_client = NetworkManagementClient(credential, subscription_id)

# Provision the virtual network and wait for completion
poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {
            "address_prefixes": ["10.0.0.0/16"]
        }
    }
)

vnet_result = poller.result()

# Step 3: Provision the subnet and wait for completion
poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, 
    VNET_NAME, SUBNET_NAME,
    { "address_prefix": "10.0.0.0/24" }
)
subnet_result = poller.result()

# Step 4: Provision an IP address and wait for completion
poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

frontend_address = poller.result()

print(f"Provisioned public IP address {frontend_address.name} with address {frontend_address.ip_address}")

# Step 5: Provision the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": subnet_result.id },
            "public_ip_address": {"id": frontend_address.id }
        }],
        "networkSecurityGroup": {
            "id": "/subscriptions/2cd750f4-c1b1-4718-a900-5391f32ef071/resourcegroups/Cloud/providers/Microsoft.Network/networkSecurityGroups/cloud-nsg"
        }
    }
)

nic_result = poller.result()

# Step 6: Provision the virtual machine

# Obtain the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

VM_NAME = "cloud-front"
USERNAME = "cloud-front"
PASSWORD = "Cloud-system2"

# Provision the VM specifying only minimal arguments, which defaults to an Ubuntu 18.04 VM
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "properties": {
            "hardwareProfile": {
                "vmSize": "Standard_D2s_v3"
            },
            "storageProfile": {
                "imageReference": {
                    "id": "/subscriptions/2cd750f4-c1b1-4718-a900-5391f32ef071/resourceGroups/Cloud/providers/Microsoft.Compute/images/cloud-front-image-20221002163839"
                },                           
                "osDisk": {
                    "caching": "ReadWrite",
                    "managedDisk": {
                        "storageAccountType": "Premium_LRS"
                    },
                    "name": "cloud-front-disk",
                    "createOption": "FromImage"
                }
            },
            "osProfile": {
                "computer_name": VM_NAME,
                "admin_username": USERNAME,
                "admin_password": PASSWORD
            },
            "networkProfile": {
                "networkInterfaces": [
                {
                    "id": nic_result.id,
                    "properties": {
                        "primary": True
                    }
                }]
            },
            "userData": str(base64.b64encode(bytes('#!/bin/bash\nmkdir /tmp/git\ncd /tmp/git\ngit clone https://'+ str(os.environ["GITHUB_PAT"]) +'@github.com/alex-mottier/TSM_CloudSys_front_pw1\ncd TSM_CloudSys_front_pw1\nrm .env\ntouch .env\necho "VITE_BACKEND_URL=http://'+ str(backend_ip_adress)+':3000" > .env\ncurl -sL https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.0/install.sh -o install_nvm.sh 2> /tmp/test0\nbash install_nvm.sh 2> /tmp/test1\nNVM_DIR="$HOME/.nvm" 2> /tmp/test2\n[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  2> /tmp/test3\n[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  2> /tmp/test4\nnvm install node --latest 2> /tmp/test5\nnpm install 2> /tmp/test6\nnpm run build 2> /tmp/test7\ncp -r dist/* /var/www/html\n', 'utf-8')))[2:-1]
        }
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")

print(f"You can connect to the app at the following adress : {frontend_address.ip_address}")