import os
import oci
import time
import datetime
from narupa.trajectory.frame_client import FrameClient
from narupa.protocol.trajectory import GetFrameRequest
import grpc

OCID = {
    'compartment': 'ocid1.compartment.oc1..aaaaaaaathog42trqnbx2j56vnhlm5ok7w3wqq323d5jn4ol4x7aoo3nlzsa',
    #'image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaapgxu42qvsub6wj43peolwjl7ldqmyr643dexwyxzidrpswlpfyuq',
    #'image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaanaygnxaxlqmvdn2wtrzoo5ak2pau5t7yvpsu4xr3wqldegkpdr5a',
    #image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaa7z3oigk4mh4dirxzwusvcldp6s7lhratzpbzbaywsxew62h5eyfq',
    'image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaatm3ehj6kq72wtiguat6oe6wom32kyyyn7h2ukltphobpq3audmha',
    'git-image': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaatk7pu2m6tolle6p3ryk2awwbq6drj2cil27c2vmgwxi7bbbzwpwa',
    'subnet': 'ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaamyov5n3yvt33o3s7pmbtbkvexj4dbfwpmagrgahgnzdsziaubdfa',
    'availability_domain': 'DpyF:EU-FRANKFURT-1-AD-3',
#    'availability_domain': 'DpyF:UK-LONDON-1-AD-2',
    'compute_shape': 'VM.GPU2.1',
#    'compute_shape': 'VM.GPU3.1',
}
IMAGES = {
    'ase': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaa7z3oigk4mh4dirxzwusvcldp6s7lhratzpbzbaywsxew62h5eyfq',
    'omm': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaatm3ehj6kq72wtiguat6oe6wom32kyyyn7h2ukltphobpq3audmha',
    #'git': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaatmf2gppemmqfmvjmdt5igs5oo2tbdudeusdgvzwgaztomioczvca',
    #'git': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaajmpum7au7tc32hskjq77b5cicjpa3yqyc65kbukyo6pcasvxsf3a',
    'git': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaaauscs5yvcd4kpmjbdotmrfikmytnk5srwkbqdfz6gfbmtb4zekja',
}
IMAGES['default'] = IMAGES['omm']
NAMESPACE = 'uobvr'
BUCKET = 'naas-bucket'
LIFECYCLE_STATE_PROVISIONING = oci.core.models.Instance.LIFECYCLE_STATE_PROVISIONING
NARUPA_PORT = 38801

INSTANCE_PARAM = {
    'Frankfurt': {
        'images': {
            #'git': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaaauscs5yvcd4kpmjbdotmrfikmytnk5srwkbqdfz6gfbmtb4zekja',
            'git': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaahv227kiffm5kzrjy4dzlxlilat3lyhwmpsxfvaeg2qt2ofciehsa',
            'ase': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaa7z3oigk4mh4dirxzwusvcldp6s7lhratzpbzbaywsxew62h5eyfq',
            'omm': 'ocid1.image.oc1.eu-frankfurt-1.aaaaaaaatm3ehj6kq72wtiguat6oe6wom32kyyyn7h2ukltphobpq3audmha',
        },
        'subnet': 'ocid1.subnet.oc1.eu-frankfurt-1.aaaaaaaamyov5n3yvt33o3s7pmbtbkvexj4dbfwpmagrgahgnzdsziaubdfa',
        'availability_domain': 'DpyF:EU-FRANKFURT-1-AD-3',
        'compute_shape': 'VM.GPU2.1',
    },
    'London': {
        'images': {
            'git': 'ocid1.image.oc1.uk-london-1.aaaaaaaavyeaeqlhuoer5efyb5dlzdza4ipr2qxuebruzczugzee5u4bsihq',
        },
        'subnet': 'ocid1.subnet.oc1.uk-london-1.aaaaaaaaf7nx3mnvh6yp4dwnpk4otbb6i2k2egvhduokctcf7bnmyumja2aq',
        'availability_domain': 'DpyF:UK-LONDON-1-AD-2',
        'compute_shape': 'VM.GPU3.1',
    },
}


class NotEnoughRessources(Exception):
    pass


def make_credentials():
    try:
        config = oci.config.from_file()
    except oci.exceptions.ConfigFileNotFound:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        #signer = oci.auth.signers.get_resource_principals_signer()
        return {'config': {}, 'signer': signer}
    return {'config': config}


def launch_compute_instance(
        filename='helen.xml',
        region='Frankfurt',
        image='git',
        extra_meta={}
    ):
    with open(os.path.expanduser('~/.ssh/id_rsa.pub')) as infile:
        ssh_key = infile.read()
    metadata = dict(filename=filename, ssh_authorized_keys=ssh_key, **extra_meta)
    compartment_id = OCID['compartment']

    compute_client = oci.core.ComputeClient(**make_credentials())
    compute_composite = oci.core.ComputeClientCompositeOperations(compute_client)
    instance_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=INSTANCE_PARAM[region]['availability_domain'],
        compartment_id=compartment_id,
        image_id=INSTANCE_PARAM[region]['images'][image],
        shape=INSTANCE_PARAM[region]['compute_shape'],
        subnet_id=INSTANCE_PARAM[region]['subnet'],
        metadata=metadata,
    )
    try:
        response = compute_composite.launch_instance_and_wait_for_state(
                instance_details,
                wait_for_states=[LIFECYCLE_STATE_PROVISIONING],
                waiter_kwargs={'max_interval_seconds': 1},
            )
    except oci.exceptions.ServiceError as error:
        if error.code == 'LimitExceeded':
            raise NotEnoughRessources
        raise error
    instance_id = response.data.id
    return instance_id


def _get_public_ip(compute_client, virtual_network_client, instance):
    vnic_attached = compute_client.list_vnic_attachments(
        compartment_id=instance.compartment_id,
        instance_id=instance.id).data
    if vnic_attached:
        vnic_id = vnic_attached[0].vnic_id
        vnic = virtual_network_client.get_vnic(vnic_id).data
        return vnic.public_ip
    return None


def _get_narupa_status(public_ip, port):
    channel = FrameClient.insecure_channel(address=public_ip, port=port)
    request = GetFrameRequest()
    try:
        channel.stub.GetFrame(request, timeout=1)
    except grpc._channel._Rendezvous as error:
        return error.code() == grpc.StatusCode.UNIMPLEMENTED
    finally:
        channel.close()
    return True


def check_instance(instance_id):
    compute_client = oci.core.ComputeClient(**make_credentials())
    virtual_network_client = oci.core.VirtualNetworkClient(**make_credentials())
    instance = compute_client.get_instance(instance_id).data
    instance_status = instance.lifecycle_state
    public_ip = _get_public_ip(compute_client, virtual_network_client, instance)
    narupa_status = False
    if public_ip:
        narupa_status = _get_narupa_status(public_ip, NARUPA_PORT)
    return (instance_status, public_ip, narupa_status)


def terminate_instance(instance_id):
    compute_client = oci.core.ComputeClient(**make_credentials())
    compute_client.terminate_instance(instance_id)


if __name__ == '__main__':
    try:
        instance_id = launch_compute_instance()
    except NotEnoughRessources:
        print('Sorry, could not launch a new instance. Try again latter.')
    except:
        print('Arrgh!')
        raise
    else:
        print(type(instance_id), instance_id)
        while True:
            time.sleep(5)
            print(datetime.datetime.now())
            print(check_instance(instance_id))
