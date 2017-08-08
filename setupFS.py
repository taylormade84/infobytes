#!/usr/bin/env python

from __future__ import print_function
import os
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


template = """
Version=2.0

[FRAMESTORES]
FRAMESTORE={0}  HADDR={1}   HOSTUUID={2}    ID={3}

[INTERFACES]
FRAMESTORE={0}
PROT=TCP     IADDR={4}    DEV=1
"""


def userInput():
    hostname = raw_input('Enter your hostname: ' + bcolors.OKGREEN)
    oneGig = raw_input(bcolors.ENDC + 'Enter your 1Gig ip address: ' + bcolors.OKGREEN)
    tenGig = raw_input(bcolors.ENDC + 'Enter your Highspeed (10/40/56) Gig ip address: ' + bcolors.OKGREEN)
    print(bcolors.ENDC)
    return hostname, oneGig, tenGig


def get_fs():
    sw_path = glob('/*/*/sw/cfg/sw_framestore_map')
    if len(sw_path) == 0:
        print(bcolors.FAIL + 'Unable to locate sw_framestore_map')
        print('Exiting')
        print(bcolors.ENDC)
        exit(-1)
    else:
        return sw_path[0]

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
    print(bcolors.OKBLUE + 'Backing up sw_framestore_map to sw_framestore_map.orig.<date>')
    print(bcolors.ENDC)


def active_int_list():
    """ Retruns a list of active interfaces """
    interfaces = []
    ifconfig = ['ifconfig']
    awk = ["awk", '/UP/&&/RUNNING/ {print $1}']
    p1 = sb.Popen(ifconfig, stdout=sb.PIPE)
    p2 = sb.Popen(awk, stdin=p1.stdout, stdout=sb.PIPE)

    for dev in p2.communicate()[0].strip().split('\n'):
        interfaces.append(dev.strip(':'))
    return interfaces


def map_gen(fs_file, host, house, highspeed, uuid, fsid):
    framestore_contents = template.format(host, house, uuid, fsid, highspeed)
    with open(fs_file, 'w+') as f:
        f.write(framestore_contents)


def user_input(dev_dict):
    while True:
        meta_selection = raw_input('Select the interfaces used for metadata: ')
        if meta_selection.isdigit() and int(meta_selection) <= len(dev_dict) and int(meta_selection) >= -1:
            break
        else:
            print('Selection was invalid, try again or exit with Ctrl+c')
            continue

    while True:
        data_selection = raw_input('Select the interfaces used for data: ')
        if data_selection.isdigit() and int(data_selection) <= len(dev_dict) and int(data_selection) >= -1:
            break
        else:
            print('Selection was invalid, try again or exit with Ctrl+c')
            continue
    return dev_dict[int(meta_selection)], dev_dict[int(data_selection)]

def main():
    # Obtaining Info for sw_framestore_map
    interfaces = active_int_list()
    dev_dict = {}

    for num, dev in enumerate(interfaces, 1):
        print(str(num) + ':', dev)
        dev_dict.update({num:dev})

    meta, data = user_input(dev_dict)
    print(meta, data)

#    hostname, oneGig, tenGig = userInput()
#    meta_name, data_name = get_int_names(oneGig, tenGig)
#    sw_path = get_fs()
#    uuid = get_uuid().strip()
#    fsid = get_fsid() 
#    backup(sw_path)

    # Creating new framestore_map
    #map_gen(sw_path, hostname, oneGig, tenGig, uuid, fsid) 
    


if __name__ == '__main__':
    main()
