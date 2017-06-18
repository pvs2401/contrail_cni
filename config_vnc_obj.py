#!/usr/bin/python
from vnc_api import vnc_api
from requests.exceptions import ConnectionError
from cfgm_common import exceptions as vnc_exc
from random import randint
from contrail_vrouter_api.vrouter_api import ContrailVRouterApi
import socket
import subprocess
import sys
import json
import uuid

class ConfigHandle(object):
    vnc_handle  = None
    domain = 'default-domain'
    api_server_host = 'localhost'
    tenant = 'default-project'
    def __init__(self,*args,**kwargs):
        if 'api_server_host' in kwargs:
            ConfigHandle.api_server_host = kwargs['api_server_host']
        if 'tenant' in kwargs:
            ConfigHandle.tenant = kwargs['tenant']
        try:
            ConfigHandle.vnc_handle = vnc_api.VncApi(api_server_host = self.api_server_host, tenant_name = self.tenant)
        except Exception as e:
            ConfigHandle.vnc_handle = None
            print "Error: connecting to the API server, check the API Server IP"
            sys.exit(1)

    def get_project(self,name=None):
        tenant = name and name or self.tenant
        fq_name = fq_name = ['default-domain', tenant]
        return self.vnc_handle.project_read(fq_name=fq_name)

    @staticmethod
    def fqn_to_string(fq_name):
        return ':'.join(fq_name)

    @staticmethod
    def string_to_fqn(name):
        return name.split(':')

    @staticmethod
    def get_subnet():
        return "100.64.{}.0/24".format(randint(1,254))
    
    def print_json(self,obj=None):
         print json.dumps(obj, default = self.vnc_handle._obj_serializer_all,indent=4, separators=(',', ': '))
    
    @staticmethod
    def shell_cmd(cmd):
        return subprocess.check_output(cmd, shell = True)

class ConfigTenant(ConfigHandle):
    def __init__(self,*args,**kwargs):
        if self.vnc_handle:
            pass
        else: 
            super(ConfigTenant,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])
    
    def create(self,name):
        domain = self.vnc_handle.domain_read(fq_name = ['default-domain'])
        obj = vnc_api.Project(name = name, parent_obj = domain)
        try:
            self.vnc_handle.project_create(obj)
        except:
            print "ERROR: Failed to create the project {}".format(name)

    def delete(self,name):
        domain = self.vnc_handle.domain_read(fq_name = ['default-domain'])
        proj = self.get_project(name)
        if not proj:
            return
        try:
            self.vnc_handle.project_delete(id=proj.uuid)
        except:
            print "ERROR: Failed to delete the project {}".format(name)

class ConfigVN(ConfigHandle):
    def __init__(self,*args,**kwargs):
        if self.vnc_handle:
            pass
        else: 
            super(ConfigVN,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])

    def create(self, name, subnet=None):
        print "Inside VN Create"
        fq_name = [self.domain,self.tenant,name]
        try:
            self.vnc_handle.virtual_network_read(fq_name=fq_name)
            print "Virtual Network [{}] already exists".format(self.fqn_to_string(fq_name))
            sys.exit(1)
        except vnc_exc.NoIdError:
            print "Creating Virtual Network [{}]".format(self.fqn_to_string(fq_name))
            proj_obj = self.get_project()
            self.vn_obj = vnc_api.VirtualNetwork(name=name, parent_obj=proj_obj)
            prop = vnc_api.VirtualNetworkType(forwarding_mode = 'l2',rpf='disable',)
            self.vn_obj.set_virtual_network_properties(prop)
            self.vn_obj.set_flood_unknown_unicast(True)
            (self.ipam_obj, self.ipam_subnet) = self.add_ipam()
            self.vn_obj.set_network_ipam(ref_obj = self.ipam_obj, ref_data =  vnc_api.VnSubnetsType([self.ipam_subnet]))
            self.vn_uuid = self.vnc_handle.virtual_network_create(self.vn_obj)
            if self.vn_uuid:
                print "Successfully created the virtual network [{}]".format(self.fqn_to_string(fq_name))
                return True
            else:
                print "Error: Cannot create the virtual network"
                return False

    def delete(self,name):
        fq_name = [self.domain,self.tenant,name]
        try:
            self.vnc_handle.virtual_network_delete(fq_name=fq_name)
            print "Deleted the virtual network [{}]".format(self.fqn_to_string(fq_name))
        except vnc_exc.NoIdError:
            print "Virtual Network  [{}] not found".format(self.fqn_to_string(fq_name))

    def read(self,name):
        fq_name = [self.domain,self.tenant,name]
        try:
            return self.vnc_handle.virtual_network_read(fq_name=fq_name)
        except vnc_exc.NoIdError:
            print "Virtual Network  [{}] not found".format(self.fqn_to_string(fq_name))
            raise

    @property
    def uuid(self,name):
        return self.read(name).uuid

    def show(self,name):
        self.print_json(self.read(name))

    def list(self):
        raise NotImplementedError

    def add_ipam(self,name='default-network-ipam',tenant='default-project',subnet=None):
        fq_name = [self.domain,tenant,name]
        cidr = self.get_subnet()
        print "Allocated CIDR for this Virtual Network is {}".format(cidr)
        print "Adding the subnet to the IPAM"
        try:
            ipam_obj = self.vnc_handle.network_ipam_read(fq_name=fq_name)
            (prefix, netlen) = cidr.split('/')
            subnet = vnc_api.SubnetType(ip_prefix = prefix, ip_prefix_len = int(netlen))
            ipam_subnet = vnc_api.IpamSubnetType(subnet = subnet, default_gateway = None) 
            return (ipam_obj, ipam_subnet)
        except vnc_exc.NoIdError:
            print "Error reading the IPAM"
            raise

class ConfigVM(ConfigHandle):
    def __init__(self,*args,**kwargs):
        if self.vnc_handle:
            pass
        else: 
            super(ConfigVM,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])

    def create(self, name):
        fq_name = [ name ]
        try:
            vm_obj = self.vnc_handle.virtual_machine_read(fq_name = fq_name)
            print "Virtual Machine exists"
            return vm_obj.uuid
        except vnc_exc.NoIdError:
            vm_obj = vnc_api.VirtualMachine(name = name)
            vm_id = self.vnc_handle.virtual_machine_create(vm_obj)
            if vm_id:
                print "Successfully creted the virtual-machine object [{}]".format(vm_id)
                return vm_id
            else:
                print "Error, failed to create the virtual machine"
                raise

    def delete(self,name):
        fq_name = [ name ]
        try:
            self.delete_vmis(name)
            self.vnc_handle.virtual_machine_delete(fq_name = fq_name)
            print "Deleted the virtual machine [{}]".format(self.fqn_to_string(fq_name))
        except vnc_exc.NoIdError:
            print "Virtual Machine  [{}] not found".format(self.fqn_to_string(fq_name))
            raise

    def delete_vmis(self,name=None):
        vm_obj = self.read(name)
        try:
            for p in vm_obj.get_virtual_machine_interface_back_refs():
                vmi_obj = self.vnc_handle.virtual_machine_interface_read(fq_name = p['to'])
                if vmi_obj.get_instance_ip_back_refs():
                    for p in vmi_obj.get_instance_ip_back_refs():
                        iip_obj = self.vnc_handle.instance_ip_read(fq_name = p['to'])
                        fq_name = iip_obj.get_fq_name()
                        self.vnc_handle.instance_ip_delete(fq_name=fq_name)
                fq_name = vmi_obj.get_fq_name()
                self.vnc_handle.virtual_machine_interface_delete(fq_name=fq_name)
            return
        except TypeError:
            return

    def read(self,name):
        fq_name = [ name ]
        try:
            return self.vnc_handle.virtual_machine_read(fq_name=fq_name)
        except vnc_exc.NoIdError:
            print "Virtual Machine  [{}] not found".format(self.fqn_to_string(fq_name))
            sys.exit(1)
    @property
    def uuid(self,name):
        return self.read(name).uuid

    def show(self,name):
        self.print_json(self.read(name))

class ConfigVMI(ConfigHandle):
    def __init__(self,*args,**kwargs):
        if self.vnc_handle:
            pass
        else: 
            super(ConfigVMI,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])

    def create(self,network,vm,name=None,address=None,sg=None):
        update = False
        if not name:
            name = str(uuid.uuid4())
        fq_name = [self.domain, self.tenant , name]
        try:
            self.vnc_handle.virtual_machine_interface_read(fq_name = fq_name)
            print "Virtual Machine Interface exists"
            return vm_obj.uuid
        except vnc_exc.NoIdError:
            proj_obj = self.get_project()
            vmi_obj = vnc_api.VirtualMachineInterface(name=name,parent_obj=proj_obj)
            self.add_network(vmi_obj,network)
            vmi_id = self.vnc_handle.virtual_machine_interface_create(vmi_obj)
            self.add_iip(vmi_obj,network)
            self.add_vm(vmi_obj,vm)
            self.vnc_handle.virtual_machine_interface_update(vmi_obj)
            if vmi_id:
                print "Successfully creted the virtual-machine interface object [{}]".format(vmi_id)
                return vmi_id
            else:
                print "Error, failed to create the virtual machine"
                raise

    def delete(self,name):
        self.delete_iip(name)
        fq_name = [self.domain, self.tenant, name ]
        try:
            self.vnc_handle.virtual_machine_interface_delete(fq_name = fq_name)
            print "Deleted the Virtual Machine Interface [{}]".format(self.fqn_to_string(fq_name))
        except:
            print "Virtual Machine Interface [{}] not found".format(self.fqn_to_string(fq_name))
            raise
            
    def add_network(self, obj, network):
        fq_name = [self.domain, self.tenant, network]
        vn_obj = self.vnc_handle.virtual_network_read(fq_name = fq_name)
        obj.add_virtual_network(vn_obj)

    def add_vm(self,obj,vm):
        fq_name = [ vm ]
        vm_obj = self.vnc_handle.virtual_machine_read(fq_name = fq_name)
        obj.add_virtual_machine(vm_obj)

    def add_iip(self,obj,network):
        vn_fq_name = [self.domain, self.tenant, network]
        vn_obj = self.vnc_handle.virtual_network_read( fq_name = vn_fq_name)
        id = str(uuid.uuid4())
        print id
        iip_obj = vnc_api.InstanceIp(name=id)
        iip_obj.add_virtual_network(vn_obj)
        iip_obj.set_instance_ip_family('v4')
        iip_obj.add_virtual_machine_interface(obj)
        self.vnc_handle.instance_ip_create(iip_obj)

    def read(self,name):
        fq_name = [self.domain, self.tenant, name ]
        try:
            return self.vnc_handle.virtual_machine_interface_read(fq_name=fq_name)
        except vnc_exc.NoIdError:
            print "Virtual Machine  Interface [{}] not found".format(self.fqn_to_string(fq_name))
            raise
    @property
    def uuid(self,name):
        return self.read(name).uuid

    def delete_iip(self,name=None):
        vmi_obj = self.read(name)
        if vmi_obj.get_instance_ip_back_refs():
            for p in vmi_obj.get_instance_ip_back_refs():
                iip_obj = self.vnc_handle.instance_ip_read(fq_name = p['to'])
                fq_name = iip_obj.get_fq_name()
                self.vnc_handle.instance_ip_delete(fq_name=fq_name)
        return

    @property
    def mac(self,name=None):
        vmi_obj = self.read(name)
        return vmi_obj.virtual_machine_interface_mac_addresses.mac_address[0]

class ConfigCNI(ConfigHandle):
    def __init__(self,**kwargs):
        if self.vnc_handle:
            pass
        else: 
            super(ConfigCNI,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])

        self.vmi = ConfigVMI()
        self.vm = ConfigVM()
        self.vn = ConfigVN()
        self.vrouter = ContrailVRouterApi()
    
    def create(self,name,vn):
        self.name = name
        cmd = 'docker inspect -f "{{.State.Pid}}" %s' %(name)
        pid = self.shell_cmd(cmd)
        pid = pid.rstrip('\n')
        self.shell_cmd('mkdir -p /var/run/netns')
        self.shell_cmd('sudo ln -sf /proc/%s/ns/net /var/run/netns/%s' %(pid,name))
        vm_name = '%s-%s' % (socket.gethostname(), name)
        try:
            vm_obj = self.vm.read(vm_name)
        except:
            self.vm.create(vm_name)
        vm_obj = self.vm.read(vm_name)
        ifl = self.get_vethid(name)
        ifl = 1024 if not ifl else int(ifl)+1
        (veth,cni) = ("veth-{}".format(str(ifl)),"cni-{}".format(str(ifl)))
        try:
            vmi_obj = self.vmi.read(cni)
        except:
            self.vmi.create(vn,vm_name,cni)
            vmi_obj = self.vmi.read(cni)

        if vmi_obj:
            mac = vmi_obj.virtual_machine_interface_mac_addresses.mac_address[0]
            self.shell_cmd('sudo ip link add %s type veth peer name %s' \
                               %(cni,veth))
            self.shell_cmd('sudo ifconfig %s hw ether %s'\
                               %(veth,mac))
            self.shell_cmd('sudo ip link set %s netns %s' \
                               %(veth, name))
            self.shell_cmd('sudo ip netns exec %s ip link set %s up' \
                               %(name,veth))
            self.shell_cmd('sudo ip link set %s up' \
                               %(cni))
        self.register_cni(name,cni,vm_obj,vmi_obj)

    def delete(self,name):
        vm_name = '%s-%s' % (socket.gethostname(), name)
        ifl = self.get_vethid(name)
        if ifl:
            cni = "cni-{}".format(str(ifl))
        else:
            print "No more interfaces are left inside the container instance"
            print "Deleting the VM object"
            self.vm.delete(vm_name)
            sys.exit(1)
        vmi_obj = self.vmi.read(cni)
        self.unregister_cni(vmi_obj)
        self.vmi.delete(cni)
        self.shell_cmd('sudo ip link delete %s' \
                       %(cni))
        return

    def list(self,name):
        import re
        from operator import attrgetter,itemgetter
        vm_name = '%s-%s' % (socket.gethostname(), name)
        vm_obj = self.vm.read(vm_name)
        vm_name = vm_obj.display_name
        try:
            print "{:24}{:24}{:24}{:24}".\
                    format('Docker Instance','Container Interface',\
                         'Vrouter interface','Network Segment')
            vmi_objs = vm_obj.get_virtual_machine_interface_back_refs()
            vmi_objs.sort(key= lambda vmi:vmi['to'][2])

            for p in vmi_objs:
                vmi_obj = self.vnc_handle.virtual_machine_interface_read(fq_name = p['to'])
                cni_name = vmi_obj.display_name
                veth_name = re.sub(r'cni','veth',cni_name)
                vn_name = vmi_obj.virtual_network_refs[0]['to'][2]
                print "{:24}{:24}{:24}{:24}".format(name,veth_name,cni_name,vn_name)
        except:
            return
        return

    def register_cni(self,name,cni,vm_obj,vmi_obj):
        mac = vmi_obj.virtual_machine_interface_mac_addresses.mac_address[0]
        self.vrouter.add_port(vm_obj.uuid, vmi_obj.uuid, cni, mac, port_type='NovaVMPort')
        return

    def unregister_cni(self,vmi_obj):
        self.vrouter.delete_port(vmi_obj.uuid)
        return
    
    def get_vethid(self,name):
        cmd = "ip netns exec %s ip link | grep veth | \
        awk '{print $2}' | awk -F ':' '{print $1}' | \
        awk -F 'veth-' '{print $2}' | tail -n 1" %(name)
        ifl = self.shell_cmd(cmd)
        return ifl.rstrip('\n')
