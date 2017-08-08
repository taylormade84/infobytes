#!/usr/bin/env python

from __future__ import print_function
import os
import socket
from time import gmtime, strftime
from glob import glob
import subprocess as sb

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

backup_time = strftime("%Y_%b_%d_time_%H%M%S", gmtime())


sw_template = """
Version=2.0

[FRAMESTORES]
FRAMESTORE={0}  HADDR={1}   HOSTUUID={2}    ID={3}

[INTERFACES]
FRAMESTORE={0}
PROT=TCP     IADDR={4}    DEV=1
"""

net_template = """
[Local]
UUID={0}
#DisplayName=

[Interfaces]
Metadata={1}
Data={2}
Multicast={1}


[SelfDiscovery]
#Port=7555
#Scope=224.0.0.1
#TTL=1
"""

def get_fs():
    sw_path = glob('/*/*/sw/cfg/sw_framestore_map')
    if len(sw_path) == 0:
        print(bcolors.FAIL + 'Unable to locate sw_framestore_map')
        print('Exiting')
        print(bcolors.ENDC)
        exit(-1)
    else:
        return sw_path[0]

def get_netcfg():
    net_path = glob('/*/*/cfg/network.cfg')
    if len(net_path) == 0:
        print(bcolors.FAIL + 'Unable to locate network.cfg file')
        print('Exiting')
        print(bcolors.ENDC)
        exit(-1)
    else:
        return net_path[0]


def get_uuid():
    cfg_path = glob('/*/*/cfg/network.cfg')
    if len(cfg_path) == 0:
        print(bcolors.FAIL + 'Unable to locate network.cfg file')
        print(bcolors.ENDC)
        exit(-1)
    else:
        with open(cfg_path[0]) as f:
            raw_file = f.readlines()
    for line in raw_file:
        if line.startswith('UUID='):
            uuid = line.split('=')[1]
    return uuid


def get_fsid():
    cfg_path = glob('/*/*/sw/cfg/sw_storage.cfg')
    if len(cfg_path) == 0:
        print(bcolors.FAIL + 'Unable to locate sw_storage.cfg file')
        print(bcolors.ENDC)
        exit(-1)
    else:
        with open(cfg_path[0]) as f:
            raw_file = f.readlines()
    for line in raw_file:
        if line.startswith('ID='):
            fsid = line.split('=')[1]
    return fsid


def backup(path):
    dstcopy = '%s.orig.%s' % (path, backup_time)
    cmd = 'cp -p %s %s' % (path, dstcopy) 
    os.system(cmd)
    print(bcolors.OKBLUE + 'Backing up {} to {}.orig.<date>'.format(path, path))
    print(bcolors.ENDC)


def active_int_list():
    """ Retruns a list of active interfaces """
    interfaces = []
    ifconfig = ['ifconfig']
    awk = ["awk", '/UP/&&/RUNNING/ {print $1}']
    p1 = sb.Popen(ifconfig, stdout=sb.PIPE)
    p2 = sb.Popen(awk, stdin=p1.stdout, stdout=sb.PIPE)

    for dev in p2.communicate()[0].strip().split('\n'):
        if not dev.lower().startswith('lo'):
            interfaces.append(dev.strip(':'))
    if len(interfaces) < 1:
        exit(1)
    return interfaces


def map_gen(fs_file, host, house, highspeed, uuid, fsid):
    framestore_contents = sw_template.format(host, house, uuid, fsid, highspeed)
    with open(fs_file, 'w+') as f:
        f.write(framestore_contents)

def net_gen(path, uuid, meta, data):
    netcfg_contents = net_template.format(uuid, meta, data)
    with open(path, 'w+') as f:
        f.write(netcfg_contents)

def user_input(dev_dict):
    while True:
        meta_selection = raw_input('Select the row number for metadata interface: ')
        if meta_selection.isdigit() and int(meta_selection) in range(1, len(dev_dict)) \
        or meta_selection.isdigit() and int(meta_selection) == 1:
            break
        else:
            print('Selection was invalid, try again or exit with Ctrl+c')
            continue

    while True:
        data_selection = raw_input('Select the row number for data interface: ')
        if data_selection.isdigit() and int(data_selection) in range(1, len(dev_dict)) \
        or data_selection.isdigit() and int(data_selection) == 1:
            break
        else:
            print('Selection was invalid, try again or exit with Ctrl+c')
            continue
    return dev_dict[int(meta_selection)], dev_dict[int(data_selection)]

def devname_to_ip(dev_name):
    ifconfig = ['ifconfig', '{}'.format(dev_name)]
    awk = ['awk', '/inet / {print $2}']
    p1 = sb.Popen(ifconfig, stdout=sb.PIPE)
    p2 = sb.Popen(awk, stdin=p1.stdout, stdout=sb.PIPE)
    return p2.communicate()[0].strip()

    
def main():
    # Obtaining Info for sw_framestore_map
    hostname = socket.gethostname()
    if hostname == None:
        print('Unable to obtain hostname')
        exit(-1)
    interfaces = active_int_list()
    dev_dict = {}

    # Viewable User Input Selection
    for num, dev in enumerate(interfaces, 1):
        print(str(num) + ':', dev)
        dev_dict.update({num:dev})

    
    # Data Injected into sw_framestore_map 
    meta, data = user_input(dev_dict)
    meta_ip = devname_to_ip(meta)
    data_ip = devname_to_ip(data)
    sw_path = get_fs()
    uuid = get_uuid().strip()
    fsid = get_fsid() 
    backup(sw_path)

    # Creating new framestore_map
    map_gen(sw_path, hostname, meta_ip, data_ip, uuid, fsid) 
    netcfg_path = get_netcfg()
    backup(netcfg_path)
    net_gen(netcfg_path, uuid, meta, data)



if __name__ == '__main__':
    main()
