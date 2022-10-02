import exoscale

exo = exoscale.Exoscale()

zone_gva2 = exo.compute.get_zone("ch-gva-2")
security_group_web = exo.compute.create_security_group("web")
for rule in [
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTP",
        network_cidr="0.0.0.0/0",
        port="80",
        protocol="tcp",
    ),
    exoscale.api.compute.SecurityGroupRule.ingress(
        description="HTTPS",
        network_cidr="0.0.0.0/0",
        port="443",
        protocol="tcp",
    ),
]:
    security_group_web.add_rule(rule)

elastic_ip = exo.compute.create_elastic_ip(zone_gva2)

instance = exo.compute.create_instance(
    name="web1",
    zone=zone_gva2,
    type=exo.compute.get_instance_type("medium"),
    template=list(
        exo.compute.list_instance_templates(
            zone_gva2,
            "Linux Ubuntu 18.04 LTS 64-bit"))[0],
    volume_size=50,
    security_groups=[security_group_web],
    user_data=""" """.format(
    eip=elastic_ip.address,
    template_url=file_index.url),
 )