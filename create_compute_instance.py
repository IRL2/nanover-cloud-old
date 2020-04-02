import oci


config = oci.config.from_file()
config['user'] = 'ocid1.user.oc1..aaaaaaaahtozgcevfxlu462v5trk6sldbfz7hckf2cfz4nm3udjxo6puhtla'
#config['log_requests'] = True
#print(config)
#compartment_id = config["tenancy"]
compartment_id = 'ocid1.compartment.oc1..aaaaaaaathog42trqnbx2j56vnhlm5ok7w3wqq323d5jn4ol4x7aoo3nlzsa'
#compartment_id = 'ocid1.compartment.oc1..aaaaaaaasptxxmopoqn5jxqzwfca2uf7skv7iqwvkprmiur2lkl4dr6grgpq'
#imd_id = 'ocid1.compartment.oc1..aaaaaaaathog42trqnbx2j56vnhlm5ok7w3wqq323d5jn4ol4x7aoo3nlzsa'
identity = oci.identity.IdentityClient(config)
print(identity.get_user(config["user"]).data)
#print(identity.list_users(compartment_id))
#for compartment in identity.list_compartments(compartment_id).data:
#    print(compartment.name, compartment.id == imd_id, compartment.id)
print(identity.list_compartments(compartment_id).data)


compute_client = oci.core.ComputeClient(config)
virtual_network_client = oci.core.VirtualNetworkClient(config)

image = compute_client.get_image('ocid1.image.oc1.eu-frankfurt-1.aaaaaaaajgpyfsp2spy7cgtnzozm4vp4l3chtcpioloh4faqlqhkg2ofmqwq').data
subnet = virtual_network_client.get_subnet('ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaamyov5n3yvt33o3s7pmbtbkvexj4dbfwpmagrgahgnzdsziaubdfa').data

vnic_details = oci.core.models.CreateVnicDetails(
    assign_public_ip=True,
    subnet_id=subnet.id,
)
instance_details = oci.core.models.LaunchInstanceDetails(
    availability_domain='DpyF:EU-FRANKFURT-1-AD-3',
    compartment_id=compartment_id,
    #create_vnic_details=vnic_details,
    image_id='ocid1.image.oc1.eu-frankfurt-1.aaaaaaaajgpyfsp2spy7cgtnzozm4vp4l3chtcpioloh4faqlqhkg2ofmqwq',
    shape='VM.GPU2.1',
    subnet_id='ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaamyov5n3yvt33o3s7pmbtbkvexj4dbfwpmagrgahgnzdsziaubdfa',
)
compute_client.launch_instance(instance_details)
