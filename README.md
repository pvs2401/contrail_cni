**# Containarized VNF orchestration on Amazon EC2 running docker using OpenContrail vrouter for overlay on top of EC2 networking.**

## Instructions to install OpenContrail on Amazon will be added later.

### Step 1: On the docker compute node bring up vMX Container. This command has to be run on the specific docker compute node.

docker run --name R2 --privileged  -v $PWD:/u:ro    --env VCP=junos-vmx-x86-64-15.1I20161124_0651_ashgupta.qcow2 --env DEV="br0 br0"   --env VPCMEM=2000 --env VCPU=1   -d -t docker/vmx:1.6 ./launch.sh

### Step 2: Create the project on Contrail.

./topo_manager.py --api-server-host 10.0.0.48 add tenant --name demo


### Step 3 : Create a Virtual Network Segment. This is equivalent of a virtual Ethernet pseudowire to which container interfaces will connect. To connect two VNF's back to back connect both of them to the same VN.

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add net --name VN1
Inside VN Create
Creating Virtual Network [default-domain:demo:VN1]
Allocated CIDR for this Virtual Network is 100.64.134.0/24
Adding the subnet to the IPAM
Successfully created the virtual network [default-domain:demo:VN1]
root@ip-192-168-100-128:~/topology_manager#

to dump the details for a virtual network use:

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo show net --name VN1
{
    "virtual_network_properties": {
        "forwarding_mode": "l2",
        "allow_transit": null,
        "network_id": null,
        "mirror_destination": false,
        "vxlan_network_identifier": null,
        "rpf": "disable"
    },
    "fq_name": [
        "default-domain",
        "demo",
        "VN1"
    ],
    "uuid": "67232c54-4737-4282-9ed8-92ed6b1f6c02",
    "display_name": "VN1",
    "parent_type": "project",
    "perms2": {
        "owner": "cloud-admin",
        "owner_access": 7,
        "global_access": 0,
        "share": []
    },
    "id_perms": {
        "enable": true,
        "description": null,
        "creator": null,
        "created": "2017-06-18T02:41:27.632582",
        "uuid": {
            "uuid_mslong": 7431832550575129218,
            "uuid_lslong": 11446060001364241410
        },
        "user_visible": true,
        "last_modified": "2017-06-18T02:41:27.653121",
        "permissions": {
            "owner": "cloud-admin",
            "owner_access": 7,
            "other_access": 7,
            "group": "cloud-admin-group",
            "group_access": 7
        }
    },
    "flood_unknown_unicast": true,
    "port_security_enabled": true,
    "network_ipam_refs": [
        {
            "to": [
                "default-domain",
                "default-project",
                "default-network-ipam"
            ],
            "href": "http://10.0.0.48:8082/network-ipam/5f5534f8-3c83-40c5-8df3-68b843a251ad",
            "attr": {
                "ipam_subnets": [
                    {
                        "subnet": {
                            "ip_prefix": "100.64.134.0",
                            "ip_prefix_len": 24
                        },
                        "dns_server_address": "100.64.134.253",
                        "enable_dhcp": true,
                        "default_gateway": "100.64.134.254",
                        "dns_nameservers": [],
                        "dhcp_option_list": null,
                        "subnet_uuid": "fca33ddd-de90-4c57-bd1a-d79e639df602",
                        "alloc_unit": 1,
                        "host_routes": null,
                        "addr_from_start": null,
                        "subnet_name": null,
                        "allocation_pools": []
                    }
                ],
                "host_routes": null
            },
            "uuid": "5f5534f8-3c83-40c5-8df3-68b843a251ad"
        }
    ],
    "virtual_network_network_id": 4
}
root@ip-192-168-100-128:~/topology_manager#


### Step 4 : Go to the docker compute node where the the VNF container is running , create a CNI (container network interface) and attach the CNI to the docker. This will automatically map to the 1st ethernet inside the VNF and will map to different interfaces (fxp0, em1, ge-0/0/0) depending on the veth interfaces are mapped by the VNF.

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add cni --name R2 --vn VN1
Virtual Machine  [ip-192-168-100-128-R2] not found
Successfully creted the virtual-machine object [00be9c9e-9531-4136-98c9-d662c38e8ecc]
Virtual Machine  Interface [default-domain:demo:cni-1024] not found
bc23c1dd-14b0-4ad2-bbf0-f95fdd3f588e
Successfully creted the virtual-machine interface object [a9a1cd01-bc85-484d-9ad6-a52593ed3dc3]
root@ip-192-168-100-128:~/topology_manager#

### Step 5: Create more VN's and CNI's to connect additional ports on the VNF.

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add net --name VN2
Inside VN Create
Creating Virtual Network [default-domain:demo:VN2]
Allocated CIDR for this Virtual Network is 100.64.107.0/24
Adding the subnet to the IPAM
Successfully created the virtual network [default-domain:demo:VN2]
root@ip-192-168-100-128:~/topology_manager#
root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add cni --name R2 --vn VN2
Virtual Machine  Interface [default-domain:demo:cni-1025] not found
8d13e4e0-3bac-406f-8f59-a1dbd587cd8c
Successfully creted the virtual-machine interface object [f1a1ec8e-e81a-4d4e-a4f5-4125cfbfd4e3]
root@ip-192-168-100-128:~/topology_manager#
root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add cni --name R2 --vn VN2
Virtual Machine  Interface [default-domain:demo:cni-1026] not found
7b0a1a80-ab39-4f68-9ab0-32c020c1d0a6
Successfully creted the virtual-machine interface object [61bdf15d-1433-4c6d-bcc9-2810e18c2017]
root@ip-192-168-100-128:~/topology_manager#

Step 6: To display all the CNI's for a VNF container and their connections to the vrouter running on this local docker compute node.

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo list cni --name R2
Docker Instance         Container Interface     Vrouter interface       Network Segment
R2                      veth-1024               cni-1024                VN1
R2                      veth-1025               cni-1025                VN2
R2                      veth-1026               cni-1026                VN2
root@ip-192-168-100-128:~/topology_manager#

Note : To get other options and the help:

root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py -h
usage: topo_manager.py [-h] --api-server-host API_SERVER_HOST
                       [--tenant-name TENANT_NAME]
                       <Operation to be performed> ...

positional arguments:
  <Operation to be performed>

optional arguments:
  -h, --help            show this help message and exit
  --api-server-host API_SERVER_HOST
                        Contrail API server address
  --tenant-name TENANT_NAME
                        Tenant or the project for the configuration
root@ip-192-168-100-128:~/topology_manager# ./topo_manager.py --api-server-host 10.0.0.48 --tenant-name demo add --help
usage: topo_manager.py add [-h] <object> ...

positional arguments:
  <object>
    net       Add a network segment
    cni       Add a CNI for a docker container
    tenant    Add a tenant(project)

optional arguments:
  -h, --help  show this help message and exit
root@ip-192-168-100-128:~/topology_manager#

