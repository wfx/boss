# BOSS
BOSS is a installer for the "Best Operating System System".
Arch linux, what else.

I wrote my repeating reinstalling steps into a simple script.
So it fits only my needs.

Howto to try it:
- 1 Dont use it in real!
- 2 Startup a virtual machine and boot the archiso.
- 3 Install wget and get the script.
- 4 Make it executable and run it.
- 5 Dont forget step 1!

##The created partitions

vda
|-vda1 vfat  550M           /boot
|-vda2 swap  8GiB
|-vda3 btrfs Avaiable space /

##The subvolumes are

vda3 /@             /
vda3 /@home         /home
vda3 /@pkg          /var/cache/packman/pkg
vda3 /@snapshots    /.snapshots
vda3 /@btrfs        /btrfs


##Installed software
Base installation with neovim :)

have a lot of fun
