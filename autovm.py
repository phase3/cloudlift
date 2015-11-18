import numbers
import yaml
import subprocess
import argparse
import os

vm_host = os.environ.get('VM_HOST')
vm_key = os.environ.get('VM_KEY')

esxi_datastore_folder = "/vmfs/volumes/datastore1"

parser = argparse.ArgumentParser(description='ESXi automation.')
parser.add_argument('-d', '--debug', action="store_true", help='run full debug')
parser.add_argument('--host', help="user@host")
parser.add_argument('--key', help="location of private key")
parser.add_argument('command', nargs="+", help="[<args>]")

args = parser.parse_args()

if args.key:
    vm_key = args.key
if args.host:
    vm_host = args.host

def debug(msg):
    if args.debug:
        print msg

def execute(command):
    debug("executing sub-process: " + command)
    try:
        return {"returncode": 0, "result": subprocess.check_output(command, shell=True)}
    except subprocess.CalledProcessError as ex:
        return {"returncode": ex.returncode, "result": ex.output}

def remote_execute(cmd):

    command="ssh -o  UserKnownHostsFile=/dev/null -o LogLevel=quiet -i " + vm_key + " " + vm_host + " '"+cmd+"'"
    return execute(command)


def get_id_list():
    result = remote_execute("vim-cmd  vmsvc/getallvms | cut -d '[' -f 1")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return

    list = result["output"].split('\n')
    result = []

    for l in list:
        x = l.find(" ")
        if x > 0:
            id = l[0:x]
            if (id.isdigit()):
                name = l[x:len(l)].strip()
                result.append([id,name])
    debug(result)
    return result

def find_id(name):
    list = get_id_list()
    if list:
        for item in list:
            if item[1] == name:
                return item[0]


def validate_sysprep_args(sysargs):
    return True


def sysprep_list(sysargs):
    result = remote_execute("ls -1 " + esxi_datastore_folder + "/sysprep")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    print "List of sysprep images on host"
    print result
    return True

def sysprep_add(sysargs):
    return True

def do_sysprep(sysargs):
    subcmd = sysargs[1]
    if subcmd == 'list':
        sysprep_list(sysargs)
    elif subcmd == 'add':
        sysprep_add(sysargs)
    return True

def validate_template_args(tempargs):
    return True

def do_template(tempargs):
    debug("template")
    return True

def validate_vm_args(vmargs):
    return True

def vm_list(vmargs):
    #result = remote_execute("vim-cmd  vmsvc/getallvms")
    list = get_id_list()
    print "List of sysprep images on host"
    for item in list:
        print("%5s  %s" % (item[0], item[1]))
    return True

def vm_power(vmargs):
    arg = vmargs[2]
    if arg == 'status':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/power.getstate " + id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    elif arg == 'off':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/power.off " + id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'on':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/power.on " + id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'reset':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/power.reset " + id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    return True

def load_vm_config(filename):
    config = yaml.load(file(filename))
    # todo: validate
    return config

def vm_add(vmargs):

    filename = vmargs[6]
    config = load_vm_config(filename)

    mem  = config.get("memory", "1024")
    cpu  = config.get("cpu", "1")
    disk = config.get("disk")
    name = config.get("name", "ubuntu")
    user = config.get("user", "ubuntu")
    password = config.get("password", 'ubuntu')

    # check to see if VM by name already exists
    # create folder
    result = remote_execute("mkdir -p " + esxi_datastore_folder + "/" + name)

    # copy sysprep vmdk to folder
    # vm resize to customer setting
    # create seed.iso with vm metadata and account info

    # copy seed.iso to remote folder
    # create vmx with profile on cpu/mem/iso in remote folder
    # register vm with esxi
    # if requested, start vm
    return True

def vm_delete(vmargs):
    return True

def vm_snapshot(vmargs):
    arg = vmargs[2]
    if arg == 'list':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/snapshot.get " + id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'create':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/snapshot.create " + id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'remove':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/snapshot.remove " + id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'revert':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/snapshot.revert " + id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'clear':
        id = find_id(vmargs[3]) # name of vm
        if id:
            result = remote_execute("vim-cmd vmsvc/snapshot.removeall " + id )
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    return True

def do_vm(vmargs):
    subcmd = vmargs[1]
    if subcmd == 'list':
        vm_list(vmargs)
    elif subcmd == 'power':
        vm_power(vmargs)
    elif subcmd == 'add':
        vm_add(vmargs)
    elif subcmd == 'delete':
        vm_delete(vmargs)
    elif subcmd == 'snapshot':
        vm_snapshot(vmargs)
    return True

if args.command[0] == 'sysprep':
    if validate_sysprep_args(args.command):
        do_sysprep(args.command)

elif args.command[0] == 'template':
    if validate_template_args(args.command):
       do_template(args.command)

elif args.command[0] == 'vm':
    if validate_vm_args(args.command):
        do_vm(args.command)






