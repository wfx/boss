# BOSS VM Testing pattern

## Pattern
- DE/WM None
- Virtual Machine (kvm)
- Boot mode systemd-boot (UEFI)
- Scripts nounset
- Language de, en
- Localization de AT
- Blockdevices
  - vda efi(vfat32), swap(swap), root(btrfs)
  - vdb home(btrfs)
