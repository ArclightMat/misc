# Install Arch with UKI in an encrypted BTRFS partition
Documentation written to get Arch booting with UKI, using an encrypted BTRFS automatically detected by systemd.


### Initial steps

1. Load keyboard layout: `loadkeys br-abnt2` or `loadkeys us-intl`

2. Connect to the network
    - Ethernet should just work.
    - WiFi needs to be set up with iwctl: 
        - `iwctl`
        - Get device with `device list`. 
        - It should be `Powered on`. 
        - Scan with `station $(DEV) scan`.
        - Fetch list with `station $(DEV) get-networks`.
        - Connect with `station $(DEV) connect $(SSID)`.

3. Ping any page with `ping` to check if network is working.

4. Check if time is accurate: `timedatectl`

### Partitioning

1. Use `gdisk` to create two partitions.
    - ESP: 512MB (GUID: EF00)
    - System: Remaining space (GUID: 8304)

2. Format EFI partition with `mkfs.vfat -F32`

3. Create encrypted system partition: `cryptsetup luksFormat`

4. Open encrypted system partition: `cryptsetup open /dev/$(part) root`

5. SSD performance tweaks: Disable workqueue and allow discards: `cryptsetup --perf-no_read_workqueue --perf-no_write-workqueue --allow-discards --persistent refresh root`

6. Format device: `mkfs.btrfs -L system /dev/mapper/root`

### Creating BTRFS subvolumes

The following setup was designed considering a personal machine, which shouldn't be running anything worthwhile in /srv or using /root.
Otherwise, follow OpenSUSE's layout instead.

Create subvolumes for root, home, swapfile and var, and a snapshot subvolume for root.
  - `/` -> `@root`
  - `/home` -> `@home`
  - `/swap` -> `@swap`
  - `/var` -> `@var`
  - `@root-snapshots`, to be configured later.

1. Mount `/dev/mapper/root` to `/mnt`: `mount -o compress=zstd /dev/mapper/root /mnt`.

2. Run `btrfs subvolume create /mnt/$(VOL)` for each volume defined previously.

3. Run `umount /mnt`.

### Mounting partitions

1. Mount @root subvolume in /mnt: `mount -o compress=zstd,subvol=@root /dev/mapper/root /mnt`.

2. Create folders in `/mnt` for each subvolume.

3. Create folder `efi` in `mnt` for EFI partition, mount it.

5. Mount each subvolume. `@var` and `@swap` should have CoW disabled.
  - No CoW: `mount -o nodatacow,subvol=@xxx /dev/mapper/root /mnt/xxx`.
  - Compression: `mount -o compress=zstd,subvol=@xxx /dev/mapper/root /mnt/xxx`.

6. SWAP: After mounting `@swap`, run `btrfs filesystem mkswapfile --size $(SWAP_SIZE)g --uuid clear /mnt/swap/swapfile` and run `swapon /mnt/swap/swapfile`.

# Packages and configuration
Personal package choice brings in `base-devel` for AUR, `linux-lts` as a fallback, `bash-completion` and `openssh` for convenience, and required packages for proper `man` and `info` support.
For filesystems, only btrfs-progs is really required, others are for convenience as they are used daily.
`networkmanager` and `neovim` as my personal picks for networking and text editing.
`amd-ucode` should be replaced with `intel-ucode` in Intel machines.

1. Install packages: `pacstrap -K /mnt base base-devel linux linux-lts linux-firmware networkmanager neovim openssh man-db man-pages texinfo bash-completion btrfs-progs dosfstools exfatprogs e2fsprogs ntfs-3g amd-ucode`.

2. Generate fstab with `genfstab -U /mnt >> /mnt/etc/fstab`

3. Enter the new installed system with `arch-chroot /mnt`

4. Set timezone with `ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime` and sync HW clock with `hwclock --systohc`.

5. Uncomment locales in `/etc/locale.gen` and run `locale-gen`.

6. Set locale with `echo "LANG=en_US.UTF-8" >> /etc/locale.conf`

7. Set keymap with `echo "KEYMAP=br-abnt2" >> /etc/vconsole.conf`

8. Set hostname in `/etc/hostname`.

9. Set root password with `passwd`.

10. Edit `/etc/mkinitcpio.conf`.
    - Replace `udev` with `systemd`.
    - Replace `keymap` and `consolefont` with `sd-vconsole`.
    - Add `sd-encrypt` before `filesystems`.

11. Update presets in `/etc/mkinitcpio.d/*.preset`
    - Uncomment `$(PRESET)_uki` and `$(PRESET)_options`

12. Create `/etc/kernel/cmdline` if it doesn't exist and add the required kernel parameters there.
    - Optionally: Create `fallback_cmdline` for fallback preset if you need different parameters.
    - Baseline parameters: `rw quiet rootflags=subvol=@root`
        - `rootflags` can be removed if `btrfs subvolume set-default` was run before.

13. Run `mkinitcpio -P` to regenerate the images.

14. Install systemd-bootloader with `bootctl install`.

15. Reboot and check it everything works.

### Post-install

1. Login and create a new user: `useradd -m -G wheel -s bash $(USER) && passwd $(USER)`.

2. Enable 'wheel' to use sudo. `EDITOR=nvim visudo`.

3. Lock `root`: `passwd -l root`.

4. Install applications, configure things.

### Secure Boot

1. Install `sbctl`. Make sure to enable Secure Boot and enable Setup Mode.

2. Create keys with `sbctl create`.

3. Enroll created keys alongside Microsoft's keys: `sbctl enroll-keys -m`

4. Sign files listed in `sbctl verify` using `sbctl sign-all`.

5. Enable `systemd-boot-update.service`, put signed files in systemd folder with `sbctl sign -s -o /usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed /usr/lib/systemd/boot/efi/systemd-bootx64.efi`

6. Reboot and check if it is working with `sbctl status`.

### Automatic LUKS decrypt with TPM2 (Requires Secure Boot)

1. Install `tpm2-tss`.

2. Get the path for the tpm2 device with `systemd-cryptenroll --tpm2-device=list`.

3. Enroll a new key and tie it to the Secure Boot state: `systemd-cryptenroll --tpm2-device=/path/to/tpm2_device /dev/sdX`

