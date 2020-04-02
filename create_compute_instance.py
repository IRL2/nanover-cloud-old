import oci

OCID = {
    'user': 'ocid1.user.oc1..aaaaaaaahtozgcevfxlu462v5trk6sldbfz7hckf2cfz4nm3udjxo6puhtla',
    'compartment': 'ocid1.compartment.oc1..aaaaaaaathog42trqnbx2j56vnhlm5ok7w3wqq323d5jn4ol4x7aoo3nlzsa',
    'image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaajgpyfsp2spy7cgtnzozm4vp4l3chtcpioloh4faqlqhkg2ofmqwq',
    'subnet': 'ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaamyov5n3yvt33o3s7pmbtbkvexj4dbfwpmagrgahgnzdsziaubdfa',
    'availability_domain': 'DpyF:EU-FRANKFURT-1-AD-3',
    'compute_shape': 'VM.GPU2.1',
}


class NotEnoughRessources(Exception):
    pass


def launch_compute_instance():
    config = oci.config.from_file()
    config['user'] = OCID['user']
    compartment_id = OCID['compartment']

    compute_client = oci.core.ComputeClient(config)
    instance_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=OCID['availability_domain'],
        compartment_id=compartment_id,
        image_id=OCID['image'],
        shape=OCID['compute_shape'],
        subnet_id=OCID['subnet'],
    )
    try:
        response = compute_client.launch_instance(instance_details)
    except oci.exceptions.ServiceError as error:
        if error.code == 'LimitExceeded':
            raise NotEnoughRessources
        raise error
    instance_id = response.data.id
    return instance_id


if __name__ == '__main__':
    try:
        launch_compute_instance()
    except NotEnoughRessources:
        print('Sorry, could not launch a new instance. Try again latter.')
    except:
        print('Arrgh!')
