#!/usr/bin/python
import sys
import argparse
from config_vnc_obj import *
import pdb
'''
Author: Vivekananda Shenoy
Email: vshenoy@juniper.net
'''

class ParseArgs:
    def __init__(self):
        pass

    def parse_args(self):
        self.p = argparse.ArgumentParser()
        self.p.add_argument('--api-server-host', help = 'Contrail API server address',required = True)
        self.p.add_argument('--tenant-name', help = 'Tenant or the project for the configuration', default='default-project')
        
        op_parser = self.p.add_subparsers(metavar = '<Operation to be performed>')
        opp_add = op_parser.add_parser('add')
        opp_del = op_parser.add_parser('del')
        opp_show = op_parser.add_parser('show')
        opp_list = op_parser.add_parser('list')

        p_add = opp_add.add_subparsers(metavar = "<object>")
        p_del = opp_del.add_subparsers(metavar = "<object>")
        p_list = opp_list.add_subparsers(metavar = "<object>")
        p_show = opp_show.add_subparsers(metavar = "<object>")

        pvn = p_add.add_parser('vn', help = 'Create Virtual Network')
        pvn.set_defaults(obj_class = ConfigVN, obj_func = 'create')
        pvn.add_argument('--name', required = True, metavar = '<Name>', help = "Name of the virtual network")
        pvn.add_argument('--subnet', metavar = '<Subnet>', required=False, help = "Subnet for the virtual network")

        pvn = p_del.add_parser('vn', help = 'Delete Virtual Network')
        pvn.set_defaults(obj_class = ConfigVN, obj_func = 'delete')
        pvn.add_argument('--name', required = True, metavar = '<Name>', help = "Name of the virtual network")

        pvn = p_list.add_parser('vn', help = 'List the Virtual Networks in this project')
        pvn.set_defaults(obj_class = ConfigVN, obj_func = 'list')

        pvn = p_show.add_parser('vn', help = 'Display details for a Virtual Network')
        pvn.set_defaults(obj_class = ConfigVN, obj_func = 'show')
        pvn.add_argument('--name', required = True, metavar = '<Name>', help = "Name of the virtual network")
        self.arguments = self.p.parse_args()
        self.run_manager()

    def run_manager(self):
        arg_list = vars(self.arguments)
        ConfigObjType = arg_list.pop('obj_class')
        config_obj_handle = ConfigObjType(api_server=arg_list.pop('api_server_host'), tenant=arg_list.pop('tenant_name'))
        pdb.set_trace()
        config_obj_oper = getattr(config_obj_handle,arg_list.pop('obj_func'))
        config_obj_oper(**arg_list)

if __name__ == '__main__':
    var1 = ParseArgs()
    var1.parse_args()
