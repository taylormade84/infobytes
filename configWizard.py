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
# Stone+Wire network configuration file
#
# This file describes the framestores on a network, and how the local machine
# communicates to other framestores on the network.
#
# Notes: If you are running sw_probed in Self-Discovery mode, there might not
#        be a need to configure this file.  Check sw_framestore_dump output
#        to verify if the default configuration fits your needs.
#
#        This configuration only applies to Stone+Wire processes.
#        Wiretap processes use /opt/Autodesk/sw/cfg/network.cfg.
#        In common scenarios, the information in both files should be
#        consistent.

Version=2.0

[FRAMESTORES]
# This section defines the remote framestores that are connected to your
# network that you wish to have access to.  For each framestore, you must have
# the following information:
#
# FRAMESTORE This specifies the name of the framestore.  Although the convention
#            is to use the current host name, you can give framestores any
#            arbitrary name that suits your workflow. 
#
# HADDR      This specifies the TCP/IP v4 Address of the machine that currently
#            has access to this framestore.  This TCP/IP address should be
#            available to all machines that you have on your network for
#            services such as NFS.
#
# HOSTUUID   This is an optional token which uniquely identifies a host.
#            The UUID must match the one in /opt/Autodesk/cfg/network.cfg.
#            This token is required to correctly resolve locks.
#
# FS         This is an optional token which denotes whether or not this
#            framestore has a local storage attached.  This is usually used to
#            remove a Burn node from the framestore list.  Valid values for
#            this token are Yes or No; Yes is the default.
#
# ID         This token is provided for legacy purposes.  The value in the 
#            /opt/Autodesk/sw/cfg/sw_storage.cfg supersedes this one.
#
# Example:
#
# FRAMESTORE=flame   HADDR=192.0.2.30  HOSTUUID=ABCDABCD-1234-3456-5678-ABCDEFABCDEF          ID=30 
# FRAMESTORE=smoke   HADDR=192.0.2.26  HOSTUUID=ABCDABCD-5678-7890-9012-ABCDEFABCDEF  FS=NO   ID=26
# FRAMESTORE=smkmac  HADDR=192.0.2.38  HOSTUUID=ABCDABCD-0912-1234-3456-ABCDEFABCDEF  FS=YES  ID=38

FRAMESTORE={0}  HADDR={1}   HOSTUUID={2}    ID={3}

[INTERFACES]
# This section defines how the local machine communicates to the other
# framestores.  It should define the best possible or only communication method
# between the local framestore and another framestore.  The local framestore
# should define all possible interfaces, whereas the all foreign framestores
# must only define the best or only method.
#
# This section is optional, when not specified the IP addresses specified
# in the [FRAMESTORE] section will be used.
#
# FRAMESTORE This is the framestore name used in the FRAMESTORES section above.
#
# PROT       This specifies the protocol to use to communicate with the
#            specified framestore.  You currently have two choices: TCP for
#            framestores connected to TCP/IP hosts and IB_SDP for framestores
#            connected to InfiniBand hosts.
#
# IADDR      The interface IP address matching the specified protocol
#
# DEV        DEV is a historical value.  It is currently always set to 1 and
#            is ignored.
#
# Example:
#
# FRAMESTORE=flame
# PROT=IB_SDP  IADDR=10.10.11.20  DEV=1

FRAMESTORE={0}
PROT=TCP     IADDR={4}    DEV=1
"""

net_template = """
[Local]
# The workstation's Universally Unique Identifier (UUID) is automatically
# generated by the application installer.  Once assigned, the UUID should
# never be edited as it uniquely identifies the workstation and the resources
# it controls. Having different workstations using the same UUID will result
# in conflicts.
#
UUID={0}

# The DisplayName is the human-readable equivalent of the UUID and is the name
# displayed in the UI to identify the workstation. Does not have to be unique,
# but it helps if all effects and finishing workstations on a network use a
# different DisplayName so the users can know which is which.
#
# On Linux, this will usually map by default to the current hostname.
#
# On Mac, this will usually map by default to the computer in the
# system preference.
#
#DisplayName=

[Interfaces]

# Comma separated list of the local network interfaces to be used for
# metadata operations. Metadata operations are usually small IO operations that
# may degrade performance when done on a high speed network adapter when a
# lower speed adapter can be used instead.
#
# The order of the interfaces in the list is the order in which they
# will be tried.
#
# If left empty, all active interfaces will be used.
#
# Example: Metadata=eth2,eth1   (on Linux)
#          Metadata=en1,en0     (on Mac)
#
Metadata={1}

# Comma separated list of the local network interfaces to be used for
# large data operations.
#
# The order of the interfaces in the list is the order in which they
# will be tried.
#
# If left empty, all active interfaces will be used.
#
# Example: Data=ib1,eth2    (on Linux)
#          Data=en1,en2     (on Mac)
#
Data={2},{1}

# Comma separated list of the local network interfaces to be used to limit
# multicast/discovery operations.
# 
# If left empty, all active interfaces that support multicast will be used.
# 
# In a facility where all machines are connected to the same networks
# (a house network and a high speed network for example), multicasting could
# only be done on one network to reduce traffic.
#
# Example: Multicast=eth2,eth1   (on Linux)
#          Multicast=en1,en0     (on Mac)
#
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

def user_input(dev_dict, interfaces):
    while True:
        meta_selection = raw_input('Select the row number for metadata interface: ')
        if meta_selection.isdigit() and int(meta_selection) <= len(dev_dict)\
        or meta_selection.isdigit() and int(meta_selection) > 0:
            break
        else:
            print('Selection was invalid, try again or exit with Ctrl+c')
            display_options(interfaces)
            continue

    while True:
        display_options(interfaces)
        data_selection = raw_input('Select the row number for data interface: ')
        if data_selection.isdigit() and int(data_selection) <= len(dev_dict)\
        or data_selection.isdigit() and int(data_selection) > 0:
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

def display_options(interfaces):
    # Viewable User Input Selection
    dev_dict = {}
    for dev in interfaces:
        ping_ip = devname_to_ip(dev)
        cmd = ['ping', '-c1', '{}'.format(ping_ip)]
        p1 = sb.Popen(cmd, stdout=sb.PIPE, stderr=sb.PIPE)
        p1.communicate()
        exit_status = p1.returncode
        if exit_status != 0:
            print(bcolors.WARNING + 'Unable to ping all active dev - check your IP configs')
            print(bcolors.ENDC)
            exit(-2)
    
    if exit_status != 0:
        print('Unable to ping IP - check your ip addresses')
        exit(-1)
    for num, dev in enumerate(interfaces, 1):
        print(str(num) + ':', dev, devname_to_ip(dev))
        dev_dict.update({num:dev})
    return dev_dict
    
    
def main():
    # Obtaining Info for sw_framestore_map
    hostname = socket.gethostname()
    if hostname == None:
        print('Unable to obtain hostname')
        exit(-1)

    interfaces = active_int_list()
    dev_dict = display_options(interfaces)
    meta, data = user_input(dev_dict, interfaces)
    meta_ip = devname_to_ip(meta)
    data_ip = devname_to_ip(data)


    
    # Data Injected into sw_framestore_map 
    sw_path = get_fs()
    uuid = get_uuid().strip()
    fsid = get_fsid() 
    backup(sw_path)

    # Creating new framestore_map
    map_gen(sw_path, hostname, meta_ip, data_ip, uuid, fsid) 

    append_int = glob('/*/*/sw/cfg/sw_framestore_map')[0]
    if meta_ip != data_ip:
        with open(append_int, 'a') as f:
            f.write('PROT=TCP   IADDR={}    DEV=1'.format(meta_ip))

    netcfg_path = get_netcfg()
    backup(netcfg_path)
    net_gen(netcfg_path, uuid, meta, data)
    print('Restart S+W and Wiretap Services in order to apply changes')



if __name__ == '__main__':
    main()
