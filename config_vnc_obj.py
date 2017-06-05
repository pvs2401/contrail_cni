#!/usr/bin/python
from vnc_api import vnc_api
from requests.exceptions import ConnectionError
from cfgm_common import exceptions as vnc_exc
from random import randint
import sys
import pdb

class ConfigHandle(object):
    def __init__(self,*args,**kwargs):
        if 'api_server_host' not in kwargs:
            print "Error: API server host not passed"
        elif 'tenant' not in kwargs:
            self.tenant = 'default-project'
            self.api_server_host = kwargs['api_server_host']
        else:
            self.tenant = kwargs['tenant']
            self.api_server_host = kwargs['api_server_host']
        try:
            self.vnc_handle = vnc_api.VncApi(api_server_host = self.api_server_host, tenant_name = self.tenant)
        except Exception as e:
            print "Error: connecting to the API server"
            sys.exit(1)

    def fqn_to_string(self,fq_name):
        return ':'.join(fq_name)

    def string_to_fqn(self,name):
        return name.split(':')

    def get_fq_name(self,name,project=None):
        if not project:
            project = self.tenant
        fq_name = ['default-domain', project]
        fq_name.append(name)
        return fq_name

    def get_subnet(self):
        return "100.64.{}.0/24".format(randint(1,254))

class ConfigVN(ConfigHandle):
    def __init__(self,*args,**kwargs):
        super(ConfigVN,self).__init__( api_server_host=kwargs['api_server'], tenant=kwargs['tenant'])

    def create(self, name, subnet):
        print "Inside VN Create"
        fq_name = self.get_fq_name(name)
        try:
            vn_obj = self.vnc_handle.virtual_network_read(fq_name=fq_name)
            print "Virtual Network [{}] already exists".format(self.fqn_to_string(fq_name))
            sys.exit(1)
        except vnc_exc.NoIdError:
            print "Creating Virtual Network [{}]".format(self.fqn_to_string(fq_name))
            vn_obj = self.vnc_handle.
            pdb.set_trace()

    def add_ipam(self,name=None,tenant=None,subnet=None):
        name='default-network-ipam'
        tenant = 'default-project'
        fq_name = self.get_fq_name(name,tenant)
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
