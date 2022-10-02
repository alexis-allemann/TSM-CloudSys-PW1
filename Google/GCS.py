# [START compute_instances_create]
import re
import sys
from typing import Any, List
import warnings
import uuid
import google.auth
import google.auth.exceptions
from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1
import googleapiclient
import googleapiclient.discovery



def get_image_from_family(project: str, family: str) -> compute_v1.Image:
    """
    Retrieve the newest image that is part of a given family in a project.
    Args:
        project: project ID or project number of the Cloud project you want to get image from.
        family: name of the image family you want to get image from.
    Returns:
        An Image object.
    """
    image_client = compute_v1.ImagesClient()
    # List of public operating system (OS) images: https://cloud.google.com/compute/docs/images/os-details
    newest_image = image_client.get_from_family(project=project, family=family)
    return newest_image


def disk_from_image(
        disk_type: str,
        disk_size_gb: int,
        boot: bool,
        source_image: str,
        auto_delete: bool = True,
) -> compute_v1.AttachedDisk:
    """
    Create an AttachedDisk object to be used in VM instance creation. Uses an image as the
    source for the new disk.
    Args:
         disk_type: the type of disk you want to create. This value uses the following format:
            "zones/{zone}/diskTypes/(pd-standard|pd-ssd|pd-balanced|pd-extreme)".
            For example: "zones/us-west3-b/diskTypes/pd-ssd"
        disk_size_gb: size of the new disk in gigabytes
        boot: boolean flag indicating whether this disk should be used as a boot disk of an instance
        source_image: source image to use when creating this disk. You must have read access to this disk. This can be one
            of the publicly available images or an image from one of your projects.
            This value uses the following format: "projects/{project_name}/global/images/{image_name}"
        auto_delete: boolean flag indicating whether this disk should be deleted with the VM that uses it
    Returns:
        AttachedDisk object configured to be created using the specified image.
    """
    boot_disk = compute_v1.AttachedDisk()
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = source_image
    initialize_params.disk_size_gb = disk_size_gb
    initialize_params.disk_type = disk_type
    boot_disk.initialize_params = initialize_params
    # Remember to set auto_delete to True if you want the disk to be deleted when you delete
    # your VM instance.
    boot_disk.auto_delete = auto_delete
    boot_disk.boot = boot
    return boot_disk


def wait_for_extended_operation(
        operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:
    """
    This method will wait for the extended (long-running) operation to
    complete. If the operation is successful, it will return its result.
    If the operation ends with an error, an exception will be raised.
    If there were any warnings during the execution of the operation
    they will be printed to sys.stderr.
    Args:
        operation: a long-running operation you want to wait on.
        verbose_name: (optional) a more verbose name of the operation,
            used only during error and warning reporting.
        timeout: how long (in seconds) to wait for operation to finish.
            If None, wait indefinitely.
    Returns:
        Whatever the operation.result() returns.
    Raises:
        This method will raise the exception received from `operation.exception()`
        or RuntimeError if there is no exception set, but there is an `error_code`
        set for the `operation`.
        In case of an operation taking longer than `timeout` seconds to complete,
        a `concurrent.futures.TimeoutError` will be raised.
    """
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


def _create_instance(
        project_id: str,
        zone: str,
        instance_name: str,
        disks: List[compute_v1.AttachedDisk],
        machine_type: str = "n1-standard-1",
        network_link: str = "global/networks/default",
        subnetwork_link: str = None,
        internal_ip: str = None,
        external_access: bool = False,
        external_ipv4: str = None,
        accelerators: List[compute_v1.AcceleratorConfig] = None,
        preemptible: bool = False,
        spot: bool = False,
        instance_termination_action: str = "STOP",
        custom_hostname: str = None,
        delete_protection: bool = False,
        metadata: [] = [],
) -> compute_v1.Instance:
    """
    Send an instance creation request to the Compute Engine API and wait for it to complete.
    Args:
        project_id: project ID or project number of the Cloud project you want to use.
        zone: name of the zone to create the instance in. For example: "us-west3-b"
        instance_name: name of the new virtual machine (VM) instance.
        disks: a list of compute_v1.AttachedDisk objects describing the disks
            you want to attach to your new instance.
        machine_type: machine type of the VM being created. This value uses the
            following format: "zones/{zone}/machineTypes/{type_name}".
            For example: "zones/europe-west3-c/machineTypes/f1-micro"
        network_link: name of the network you want the new instance to use.
            For example: "global/networks/default" represents the network
            named "default", which is created automatically for each project.
        subnetwork_link: name of the subnetwork you want the new instance to use.
            This value uses the following format:
            "regions/{region}/subnetworks/{subnetwork_name}"
        internal_ip: internal IP address you want to assign to the new instance.
            By default, a free address from the pool of available internal IP addresses of
            used subnet will be used.
        external_access: boolean flag indicating if the instance should have an external IPv4
            address assigned.
        external_ipv4: external IPv4 address to be assigned to this instance. If you specify
            an external IP address, it must live in the same region as the zone of the instance.
            This setting requires `external_access` to be set to True to work.
        accelerators: a list of AcceleratorConfig objects describing the accelerators that will
            be attached to the new instance.
        preemptible: boolean value indicating if the new instance should be preemptible
            or not. Preemptible VMs have been deprecated and you should now use Spot VMs.
        spot: boolean value indicating if the new instance should be a Spot VM or not.
        instance_termination_action: What action should be taken once a Spot VM is terminated.
            Possible values: "STOP", "DELETE"
        custom_hostname: Custom hostname of the new VM instance.
            Custom hostnames must conform to RFC 1035 requirements for valid hostnames.
        delete_protection: boolean value indicating if the new virtual machine should be
            protected against deletion or not.
    Returns:
        Instance object.
    """
    instance_client = compute_v1.InstancesClient()

    # Use the network interface provided in the network_link argument.
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = network_link
    if subnetwork_link:
        network_interface.subnetwork = subnetwork_link

    if internal_ip:
        network_interface.network_i_p = internal_ip

    if external_access:
        access = compute_v1.AccessConfig()
        access.type_ = compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name
        access.name = "External NAT"
        access.network_tier = access.NetworkTier.STANDARD.name
        if external_ipv4:
            access.nat_i_p = external_ipv4
        network_interface.access_configs = [access]

    # Collect information into the Instance object.
    instance = compute_v1.Instance()
    instance.network_interfaces = [network_interface]
    instance.name = instance_name
    instance.disks = disks
    if re.match(r"^zones/[a-z\d\-]+/machineTypes/[a-z\d\-]+$", machine_type):
        instance.machine_type = machine_type
    else:
        instance.machine_type = f"zones/{zone}/machineTypes/{machine_type}"

    if accelerators:
        instance.guest_accelerators = accelerators

    if preemptible:
        # Set the preemptible setting
        warnings.warn(
            "Preemptible VMs are being replaced by Spot VMs.", DeprecationWarning
        )
        instance.scheduling = compute_v1.Scheduling()
        instance.scheduling.preemptible = True

    if spot:
        # Set the Spot VM setting
        instance.scheduling = compute_v1.Scheduling()
        instance.scheduling.provisioning_model = (
            compute_v1.Scheduling.ProvisioningModel.SPOT.name
        )
        instance.scheduling.instance_termination_action = instance_termination_action

    if custom_hostname is not None:
        # Set the custom hostname for the instance
        instance.hostname = custom_hostname

    if delete_protection:
        # Set the delete protection bit
        instance.deletion_protection = True

    # Wait for the create operation to complete.
    print(f"Creating the {instance_name} instance in {zone}...")

    operation = instance_client.insert(project=project_id, zone=zone, instance_resource=instance, metadata=metadata)


    wait_for_extended_operation(operation, "instance creation")

    print(f"Instance {instance_name} created.")
    return instance_client.get(project=project_id, zone=zone, instance=instance_name)

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

# create_instance(compute, project, zone, name, image, machine, ip, ip_public, tags=[], metadata=[])
compute = googleapiclient.discovery.build('compute', 'v1')
image_back="projects/cloudsys-pw1/global/images/image-back"
create_instance(compute, project_id, instance_zone, instance_name_back, image_back, "e2-micro", "10.172.0.4", BACKEND_IP,
                metadata=metadata_back, tags= ['http-server', 'https-server', 'tcp3000'])

#########################################
# FRONT
#########################################
_script_front = f"""#!/bin/bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash > /tmp/curl 2> /tmp/curl_error
nvm install v16.14.0 > /tmp/nvm_install 2> /tmp/nvm_install_error
which npm > /tmp/which_npm 2> /tmp/which_npm_error
cd /tmp
rm -rf TSM_CloudSys_front_pw1  
git clone https://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@github.com/alex-mottier/TSM_CloudSys_front_pw1.git > /tmp/clone 2> /tmp_clone_error
cd TSM_CloudSys_front_pw1
rm .env
touch .env
echo "VITE_BACKEND_URL=http://{BACKEND_IP}:3000/" > .env 
echo "VITE_BACKEND_URL=http://{BACKEND_IP}:3000/" > /tmp/emv_file
npm install 2> /tmp/npm_install_error > /build_install
npm run build 2> /tmp/npm_build_error > /npm_build
cp -r dist/* /var/www/html
"""

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
