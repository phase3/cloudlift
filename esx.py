import yaml
import subprocess
import argparse
import os

vm_host = os.environ.get('VM_HOST')
vm_key = os.environ.get('VM_KEY')

esxi_datastore_folder = "/vmfs/volumes/datastore1"

parser = argparse.ArgumentParser(description='ESXi automation.')
parser.add_argument('-v', '--verbose', action="store_true", help='show progress')
parser.add_argument('-d', '--debug', action="store_true", help='run full debug')
parser.add_argument('--host', required=False, help="user@host")
parser.add_argument('--key', required=False, help="location of private key")
parser.add_argument('command', nargs="*", help="[<args>]")

args = parser.parse_args()

def do_usage():
    print "Usage: esx [options] <command> [<args>]"
    print ""
    print "    --host               host in the form of user@host, or VM_HOST environment variable"
    print "    --key                keyfile location, or VM_KEY environment variable"
    print "    -v, --verbose        more verbosity"
    print "    -d, --debug          debug level output including remote commands to the server"
    print ""
    print "Common commands:"
    print "     vm                  vm commands are:"
    print "             list        list available vms on this server"
    print ""
    print "             add    <name> <config_template> <user_data>"
    print "                         add a new vm, parameters are:"
    print "                         name - name of new vm    "
    print "                         config_template - configuration template (in YAML)"
    print "                         user_data - cloud-init user-data file to include, see:"
    print "                                     https://cloudinit.readthedocs.org/en/latest/"
    print ""
    print "             delete <name>"
    print "                         power down and delete a vm, parameters are:"
    print "                         name - name of vm to delete"
    print ""
    print "             snapshot <action> <vm name>"
    print "                     list"
    print "                     create"
    print "                     remove"
    print "                     revert"
    print "                     clear"
    print ""
    print "             power   <action> <vm name>"
    print "                     status"
    print "                     on"
    print "                     off"
    print "                     reset"


if not args.command or len(args.command) < 1:
    print "no command provided."
    do_usage()
    exit(1)

if not args.command or len(args.command) < 2:
    print "no sub-command provided."
    do_usage()
    exit(1)

if not vm_host and not args.host:
    print "no --host parameter or VM_HOST environment variable provided."
    do_usage()
    exit(1)

if not vm_key and not args.key:
    print "no --key parameter or VM_KEY environment variable provided."
    do_usage()
    exit(1)

# override enviornment variable
if args.key:
    vm_key = args.key

# override enviornment variable
if args.host:
    vm_host = args.host


def debug(msg):
    if args.debug:
        print "DEBUG:" + msg


def verbose(msg):
    if args.verbose:
        print msg


def execute(command):
    debug("executing sub-process: " + command)
    try:
        return {"returncode": 0, "result": subprocess.check_output(command, shell=True)}
    except subprocess.CalledProcessError as ex:
        return {"returncode": ex.returncode, "result": ex.output}


def remote_execute(cmd):
    command = "ssh -o  UserKnownHostsFile=/dev/null -o LogLevel=quiet -i " + vm_key + " " + vm_host + " '" + cmd + "'"
    return execute(command)


def get_id_list():
    result = remote_execute("vim-cmd  vmsvc/getallvms | cut -d '[' -f 1")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return

    id_list = result["result"].split('\n')
    result = []

    for l in id_list:
        x = l.find(" ")
        if x > 0:
            vm_id = l[0:x]
            if vm_id.isdigit():
                name = l[x:len(l)].strip()
                result.append([vm_id, name])
    debug(str(result))
    return result


def find_id(name):
    id_list = get_id_list()
    if id_list:
        for item in id_list:
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
    list = get_id_list()
    print "List of registered VMs"
    for item in list:
        print("%5s  %s" % (item[0], item[1]))
    return True


def vm_power(vmargs):
    arg = vmargs[2]
    if arg == 'status':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/power.getstate " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    elif arg == 'off':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/power.off " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    elif arg == 'on':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/power.on " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]

    elif arg == 'reset':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/power.reset " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    else:
        print "invalid action [ " + arg + " ] for vm power command."
        do_usage()
        exit(1)
    return True


def load_vm_config(filename):
    config = yaml.load(file(filename))
    # todo: validate
    return config


def build_seed_iso(name, userdatafile):
    result = execute("rm -f user-data meta-data seed.iso")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    meta_file = open("meta-data", 'w')
    meta_file.write("instance-id: iid-local01\n")
    meta_file.write("local-hostname: " + name + "\n")
    meta_file.write("hostname: " + name + "\n")
    meta_file.close()

    result = execute("cp -f " + userdatafile + " user-data")

    result = execute("genisoimage -quiet -output seed.iso -volid cidata -joliet -rock user-data meta-data")

    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])


def vm_add(vmargs):
    name = vmargs[2]
    filename = vmargs[3]
    userdatafile = vmargs[4]

    verbose("building new instance: " + name)
    verbose(" - template : " + filename)
    config = load_vm_config(filename)

    mem = str(config.get("memory", "1024"))
    cpu = str(config.get("cpu", "1"))
    disk = config.get("disk")
    power = config.get("power")
    image = config.get("image", 'trusty-server-nocloud-amd64-disk1')

    verbose(" - image: " + image)
    # TODO check to see if VM by name already exists
    # create folder
    verbose(" - folder: " + esxi_datastore_folder + "/" + name)
    result = remote_execute("mkdir -p " + esxi_datastore_folder + "/" + name)
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    # copy sysprep vmdk to folder
    verbose(" - staging new vm...")
    result = remote_execute(
        "vmkfstools -i " + esxi_datastore_folder + "/sysprep/" + image + ".vmdk -d thin " +
        esxi_datastore_folder + "/" + name + "/" + name + ".vmdk ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])
    result = remote_execute(
        "cp " + esxi_datastore_folder + "/sysprep/" + image + ".vmx-template " +
        esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    if disk:
        verbose(" - resizing disk to: " + disk)
        result = remote_execute(
            "vmkfstools -X " + disk + " " + esxi_datastore_folder + "/" + name + "/" + name + ".vmdk ")
        if result["returncode"] != 0:
            print "Error: " + result["result"]
            return
        debug(result["result"])

    verbose(" - building seed iso... ")
    # create seed.iso with vm metadata and account info
    build_seed_iso(name, userdatafile)

    # copy seed.iso to remote folder
    result = execute(
        "scp -o  UserKnownHostsFile=/dev/null -o LogLevel=quiet -i " + vm_key + " seed.iso " +
        vm_host + ":" + esxi_datastore_folder + "/" + name)
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    result = execute("rm -f  seed.iso user-data meta-data")

    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    iso = "seed.iso"

    verbose(" - applying settings... ")
    result = remote_execute(
        "sed -i \"s/{ISO}/" + iso + "/g\" " + esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    # update vmx with profile on cpu/mem/iso in remote folder
    result = remote_execute(
        "sed -i \"s/{CPU}/" + cpu + "/g\" " + esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])
    result = remote_execute(
        "sed -i \"s/{NAME}/" + name + "/g\" " + esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])
    result = remote_execute(
        "sed -i \"s/{RAM}/" + mem + "/g\" " + esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    verbose(" - registering vm ")
    # register vm with esxi
    result = remote_execute("vim-cmd solo/registervm " + esxi_datastore_folder + "/" + name + "/" + name + ".vmx ")
    if result["returncode"] != 0:
        print "Error: " + result["result"]
        return
    debug(result["result"])

    # if requested, start vm
    if power:
        verbose(" - powering on vm. ")
        vm_id = find_id(name)
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/power.on " + vm_id + "")
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            debug(result["result"])

    return True


def vm_delete(vmargs):
    name = vmargs[2]
    if name:
        vm_id = find_id(name)  # name of vm
        if vm_id:
            verbose("deleting " + name + " (id:" + vm_id + ")")
            verbose(" - powering off vm...")
            # force power off
            result = remote_execute("vim-cmd vmsvc/power.off " + vm_id + "")
            if result["returncode"] != 0:
                print "Error: " + result["result"]
            debug(result["result"])

            verbose(" - cleaning up seed.iso...")
            # remove seed.iso
            result = remote_execute("rm -f " + esxi_datastore_folder + "/" + name + "/seed.iso")
            if result["returncode"] != 0:
                print "Error: " + result["result"]
            debug(result["result"])

            verbose(" - destroying vm...")
            # destroy
            result = remote_execute("vim-cmd vmsvc/destroy " + vm_id + "")
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            debug(result["result"])


def vm_snapshot(vmargs):
    arg = vmargs[2]
    if arg == 'list':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/snapshot.get " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            debug(result["result"])
    elif arg == 'create':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/snapshot.create " + vm_id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'remove':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/snapshot.remove " + vm_id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'revert':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/snapshot.revert " + vm_id + " " + vmargs[4])
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    elif arg == 'clear':
        vm_id = find_id(vmargs[3])  # name of vm
        if vm_id:
            result = remote_execute("vim-cmd vmsvc/snapshot.removeall " + vm_id)
            if result["returncode"] != 0:
                print "Error: " + result["result"]
                return
            print result["result"]
    else:
        print "invalid action [ " + arg + " ] for vm snapshot command."
        do_usage()
        exit(1)

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
    else:
        print "invalid vm command."
        do_usage()
        exit(1)
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
else:
    print "invalid command."
    do_usage()
    exit(1)
