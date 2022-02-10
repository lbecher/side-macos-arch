import os
import sys
import textwrap

"""
fdisk_partition_disk_string = '''
g
n
1

+1024M
y
n
2


y
t
1
1
y
t
2
30
y
w
EOF
'''
"""

boot_partition = ''
lvm_partition = ''

use_luks = ''

swap_partition_enable = ''
home_partition_enable = ''
lfs_partition_enable = ''

# General functions
def winput(string):
    return input('\n'.join(textwrap.wrap(string, width = os.get_terminal_size(0)[0], drop_whitespace = False)))


def ask_to_continue():
    choice = winput('Continue? (Type 1 for yes or any other key for no) ')
    if (choice != '1'):
        sys.exit(-1)


# Getting storage informations from user
def get_encryption_authorization():
    global use_luks
    os.system('clear')
    choice = winput('Do you want to encrypt your logical volume? (Type 1 for yes or any other key for no) ')
    if (choice == '1'):
        use_luks = '1'
    else:
        use_luks = '0'


def get_storage():
    global boot_partition
    global lvm_partition
    os.system('clear')
    os.system('lsblk -d | grep disk')
    boot_partition = winput('Type your boot partition (sda1|nvme0n1p1|...): ')
    lvm_partition = winput('Type your lvm partition (sda3|nvme0n1p3|...): ')
    print('Check your configuration:')
    print('  Boot partition: /dev/' + boot_partition)
    print('  LVM partition:  /dev/' + lvm_partition)
    ask_to_continue()


def get_volumes_configuration():
    global swap_partition_enable
    global home_partition_enable
    global lfs_partition_enable
    os.system('clear')
    swap_partition_enable = winput('Do you want to have a dedicated logical volume to swap? (Type 1 for yes or any other key for no) ')
    if (swap_partition_enable == '1'):
        print('  The swap volume is enabled.')
    home_partition_enable = winput('Do you want to have a dedicated logical volume to home? (Type 1 for yes or any other key for no) ')
    if (home_partition_enable == '1'):
        print('  The home volume is enabled.')
    lfs_partition_enable = winput('Do you want to have a dedicated logical volume to build a Linux From Scratch project? (Type 1 for yes or any other key for no) ')
    if (lfs_partition_enable == '1'):
        print('  The lfs volume is enabled.')
    ask_to_continue()


# Installation functions
def generate_fstab():
    os.system('clear')
    print('Generating fstab...')
    os.system('genfstab -pU /mnt >> /mnt/etc/fstab')
    ask_to_continue()
    os.system('clear')


def run_pacstrap():
    os.system('clear')
    print('Running pacstrap...')
    os.system('pacstrap /mnt base base-devel linux linux-firmware openssh git nano python3')
    ask_to_continue()
    generate_fstab()


def mount_volumes():
    if (boot_partition == ''):
        get_storage()
    if (swap_partition_enable == ''):
        get_volumes_configuration()
    os.system('clear')
    print('Mounting volumes into /mnt...')
    os.system('mount /dev/mapper/archlinux-root /mnt -v')
    os.system('mkdir /mnt/boot -v')
    os.system('mount /dev/' + boot_partition + ' /mnt/boot -v')
    if (swap_partition_enable == '1'):
        os.system('swapon /dev/mapper/archlinux-swap -v')
    if (home_partition_enable == '1'):
        os.system('mkdir /mnt/home -v')
        os.system('mount /dev/mapper/archlinux-home /mnt/home -v')
    ask_to_continue()
    run_pacstrap()


def set_lvm_and_filesystems():
    if (boot_partition == ''):
        get_storage()
    if (swap_partition_enable == ''):
        get_volumes_configuration()
    if (use_luks == ''):
        get_encryption_authorization()
    os.system('clear')
    if (swap_partition_enable == '1'):
        swap_partition_size = winput('Set your swap logical volume size (4G/8G/...): ')
    if (home_partition_enable == '1'):
        home_partition_size = winput('Set your home logical volume size (64G/128G/...): ')
    if (lfs_partition_enable == '1'):
        lfs_partition_size = winput('Set your lfs logical volume size (16G/24G/...): ')
    print('Setting up LVM and filesystems...')
    if (use_luks == '1'):
        os.system('pvcreate /dev/mapper/' + lvm_partition + '-crypt')
        os.system('vgcreate archlinux /dev/mapper/' + lvm_partition + '-crypt')
    else:
        os.system('pvcreate /dev/' + lvm_partition)
        os.system('vgcreate archlinux /dev/' + lvm_partition)
    if (swap_partition_enable == '1'):
        os.system('lvcreate -C y -L ' + swap_partition_size + ' -n swap archlinux')
        os.system('mkswap /dev/mapper/archlinux-swap')
    if (home_partition_enable == '1'):
        os.system('lvcreate -C y -L ' + home_partition_size + ' -n home archlinux')
        os.system('mkfs.ext4 /dev/mapper/archlinux-home')
    if (lfs_partition_enable == '1'):
        os.system('lvcreate -C n -L ' + lfs_partition_size + ' -n lfs archlinux')
        os.system('mkfs.ext4 /dev/mapper/archlinux-lfs')
    os.system('lvcreate -C n -l 100%FREE -n root archlinux')
    os.system('mkfs.ext4 /dev/mapper/archlinux-root')
    #os.system('mkfs.vfat -F32 /dev/' + boot_partition)
    ask_to_continue()
    mount_volumes()


def create_luks():
    get_encryption_authorization()
    if (use_luks == '1'):
        if (lvm_partition == ''):
            get_storage()
        os.system('clear')
        print('Setting up luks...')
        os.system('cryptsetup -c aes-xts-plain64 -s 512 -h sha512 luksFormat /dev/' + lvm_partition)
        os.system('cryptsetup luksOpen /dev/' + lvm_partition + ' ' + lvm_partition + '-crypt')
        ask_to_continue()
    set_lvm_and_filesystems()


def set_keyboard_layout():
    os.system('clear')
    layout = winput('Set up your keyboard layout (us|uk|br-abnt2): ')
    os.system('loadkeys ' + layout)
    ask_to_continue()
    create_luks()


# Initial functions
def menu():
    os.system('clear')
    print('Select a start point:')
    print('  1. Set keyboard layout')
    print('  2. Create LUKS partition')
    print('  3. Set LVM and make filesystems')
    print('  4. Mount partitions and volumes')
    print('  5. Run pacstrap')
    print('  5. Generate fstab')
    print('Type any other key to exit.')
    print('')


def init():
    os.system('clear')
    menu()
    choice = winput('Type your choice: ')
    if choice == '1':
        set_keyboard_layout()
    elif choice == '2':
        create_luks()
    elif choice == '3':
        set_lvm_and_filesystems()
    elif choice == '4':
        mount_volumes()
    elif choice == '5':
        run_pacstrap()
    elif choice == '6':
        generate_fstab()


init()
