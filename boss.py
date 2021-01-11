#!/usr/bin/python3
# encoding: utf-8
#
# BOSS: The sweet Arch Linux (GPT/EFI none dualboot) meta installer
# Copyright (C) 2021 Wolfgang Morawetz wolfgang.morawetz@gmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#        :::::::::   ::::::::   ::::::::   ::::::::   :::
#       :+:    :+: :+:    :+: :+:    :+: :+:    :+:  :+:
#      +:+    +:+ +:+    +:+ +:+        +:+         +:+
#     +#++:++#+  +#+    +:+ +#++:++#++ +#++:++#++  +#+
#    +#+    +#+ +#+    +#+        +#+        +#+
#   #+#    #+# #+#    #+# #+#    #+# #+#    #+#  #+#
#  #########   ########   ########   ########   ###
#
# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
# DOCUMENTATION ( ¯\_(ツ)_/¯ ):
# BOSS Install Layout (yaml)
#   https://github.com/wfx/boss
# Technical
#   https://yaml.org/spec/1.2/spec.html
#   https://wiki.archlinux.org/index.php/Installation_guide#Partition_the_disks
#   https://wiki.archlinux.org/index.php/Installation_guide#Format_the_partitions
#   https://wiki.archlinux.org/index.php/Btrfs
#   https://wiki.archlinux.org/index.php/Installation_guide#Mount_the_file_systems
#   https://systemd.io/DISCOVERABLE_PARTITIONS/
#   https://jlk.fjfi.cvut.cz/arch/manpages/man/systemd-gpt-auto-generator.8
#   https://en.wikipedia.org/wiki/GUID_Partition_Table#Partition_type_GUIDs
#   https://www.freedesktop.org/wiki/Specifications/DiscoverablePartitionsSpec/
#

__author__ = "Wolfgang Morawetz"
__copyright__ = "Copyright (C) 2021 Wolfgang Morawetz"
__version__ = "2021.01.08/0"
__description__ = "BOSS is a meta installer for the Best Operating System System"
__github__ = "https://github.com/wfx/boss"
__source__ = "Source code and bug reports: {0}".format(__github__)

import yaml
import requests


class Blockdevices:
    def __init__(self, template):
        self.template = template
        self.part_list = []
        self.mount_list = []
        gpt_typecodes = {
            'esp': 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B',
            'boot': 'BC13C2FF-59E6-4262-A352-B275FD6F7172',
            'swap': '0657FD6D-A4AB-43C4-84E5-0933C84B4F4F',
            'root_x86-64': '4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709',
            'home': '933AC7E1-2EB4-4F13-B844-0E14E2AEF915',
            'linux': '0FC63DAF-8483-4772-8E79-3D69D8477DE4'
        }
        for device, dev in self.template.get('Mapping').items():
            # Using section 'Mapping' to generate the part and mount list.
            for partition, part in self.template[device].items():
                self.mount_list.append(
                    {'device': device, 'partition': partition})
                self.part_list.append(self.mount_list[-1])
                if part.get('type')[0:4] == "root":
                    try:
                        item = self.mount_list.pop()
                        self.mount_list.insert(0, item)
                    except ValueError:
                        print(f"Moving item to 0 failed. List remains unchanged.")
                # Modify and adding template settings.
                self.template[device][partition].update(
                    {'device_name': dev['name']})
                self.template[device][partition].update(
                    {'partition_name': dev['name'] + partition[-1]})
                self.template[device][partition].update(
                    {'label': part.get('label', part.get('type')[0:4]).upper()})
                # Maybe overwrite the type setting.
                self.template[device][partition].update(
                    {'gpt_type': gpt_typecodes.get(part['type'], 'ERROR: Unknown partition type')})
                # Crypt...
                if part.get('crypt') == "luks":
                    self.template[device][partition].update(
                        {'crypt_mount_point': part['label'].lower()})

    def make_partition(self):
        print("# Make Partitions:...")
        for po in self.part_list:
            _ = self.template[po['device']][po['partition']]
            print(f"sgdisk -n 0:0:{_['size']} -t 0:{_['gpt_type']} -c 0:{_['label']} {_['device_name']}")

    def make_filesystem(self):
        print("# Make Filesystem:...")
        for po in self.part_list:
            _ = self.template[po['device']][po['partition']]
            _name = "/dev/" + _['partition_name']
            if _.get('crypt') == "luks":
                print(f"cryptsetup luksFormat {_name}")
                print(f"cryptsetup open {_name} {_['crypt_mount_point']}")
                _name = "/dev/mapper/" + _['crypt_mount_point']
            _format = _.get('format')
            if _format == "vfat32":
                print(f"mkfs.vfat -F32 -n {_['label']} {_name}")
            elif _format == "swap":
                print(f"mkfs.swap -L {_['label']} {_name}")
            elif _format == "btrfs":
                print(f"mkfs.btrfs -f -L {_['label']} {_name}")
                self.make_btrfs_subvolumes(_name, _.get('Subvolumes'))
            elif _format == "ext4":
                print(f"mkfs.ext4 -f -L {_['label']} {_name}")
            else:
                print("ERROR: Unknown filesystem!")

    def make_btrfs_subvolumes(self, partition, subvolumes):
        print("# - Make BTRFS Subvolumes:...")
        print(f"mount {partition} /mnt")
        for sub in subvolumes:
            print(f"btrfs sub create /mnt/{sub.get('subvolume')}")
        print("umount /mnt")

    def mount_partition(self):
        print("# Mount Partitions:...")
        for po in self.mount_list:
            _ = self.template[po['device']][po['partition']]
            _name = "/dev/" + _['partition_name']
            if _.get('crypt') == "luks":
                _name = "/dev/mapper/" + _['crypt_mount_point']
            _format = _.get('format')
            if _format == "vfat32":
                print(
                    f"mount {_name} {_.get('mount_point', 'ERROR: Missing mount point')}")
            elif _format == "swap":
                print(f"swapon {_name}")
            elif _format == "btrfs":
                self.mount_btrfs_subvolumes(_name, _.get('Subvolumes'))
            elif _format == "ext4":
                print(f"mount {_name} {_['mount_point']} ")
            else:
                print("ERROR: Unknown filesystem!")

    def mount_btrfs_subvolumes(self, part_name, subvolumes):
        print("# - Mount BTRFS Subvolumes:...")
        for sub in subvolumes:
            _mp = sub.get('mount_point', 'ERROR: Missing mount point')
            if _mp == "/":
                print(f"mount {part_name} /mnt")
                print(f"mount -o {sub.get('mount_option', 'noatime,nodiratime')},subvol={sub.get('subvolume')} {part_name} /mnt")
            else:
                print(f"mkdir -p /mnt{_mp}")
                print(f"mount -o {sub.get('mount_option', 'noatime,nodiratime')},subvol={sub.get('subvolume')} {part_name} /mnt{_mp}")


class Localization:
    def __init__(self, localization):
        self.l10n = localization
        url = "https://freegeoip.app/json/"
        headers = {'accept': "application/json",
                   'content-type': "application/json"}
        # self.geoip = requests.request("GET", url, headers=headers)

    def keyboard(self):
        kb = self.l10n.get('keyboard')
        if kb:
            print(f"loadkeys {kb}")

    def time_zone(self):
        tz = self.l10n.get('time_zone', self.geoip.json()['time_zone'])
        print(
            f"arch-chroot /mnt/ ln -sf /usr/share/zoneinfo/{tz} /etc/localtime")


class Application:
    def __init__(self, template):
        self.template = self.load_template(template)
        self.system = self.template.get('System')
        self.l10n = Localization(self.template.get('Localization'))
        self.blkd = Blockdevices(self.template.get('Blockdevices'))

    def run(self):
        self.l10n.keyboard()
        print(f"timedatectl set-ntp {self.system['system_clock']}")
        self.blkd.make_partition()
        self.blkd.make_filesystem()
        self.blkd.mount_partition()
        print("pacman -Sy archlinux-keyring")
        print("pacman-key --populate archlinux")
        print("pacman-key --refresh-keys")
        print(f"pacstrap /mnt {self.system['pacstrap']}")
        print("genfstab -U /mnt >> /mnt/etc/fstab")
        print(f"echo {self.system['hostname']} > /mnt/etc/hostname")
        # Locale...
        self.l10n.time_zone()

    def load_template(self, template):
        with open(template, 'r') as file:
            template = yaml.load(file, Loader=yaml.FullLoader)
            return template


if __name__ == "__main__":
    boss = Application("template/testing/boss.yaml")
    boss.run()
