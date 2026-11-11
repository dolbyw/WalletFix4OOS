#!/usr/bin/env python3
"""Build a CPH2449 KernelSU module from the official 2.3.0 ZIP and PHB110 files."""

import argparse
import hashlib
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


BASE_SHA256 = "E36C262046DA7CABA4DD656EA7E413BE36E3ABEE9F87956E26A92F85B0DEC706"
COMPONENTS = {
    "system/product/priv-app/KeKeUserCenter/KeKeUserCenter.apk": (
        "usercenter/KeKeUserCenter.apk",
        "56E65CDA7DAB732A514A04A3832B93E721D6526C2E81080FC1B6E9FAF0943E81",
    ),
    "system/product/priv-app/KeKeUserCenterAccount/KeKeUserCenterAccount.apk": (
        "usercenter_account/KeKeUserCenterAccount.apk",
        "780321D251A8A178251E8F169FF0133C64922D7C7A017B07E5EC6B68B4F35ACC",
    ),
    "system/product/priv-app/OpenID/OpenID.apk": (
        "openid/OpenID.apk",
        "5E79220E6E3838B5E1FBCA6C86CE0BB069321773A578D43D9CCEC9B57A1A9AC4",
    ),
    "system/product/app/TasWallet/TasWallet.apk": (
        "walletfix_phb_components/TasWallet/TasWallet.apk",
        "E7CA8CA5542BC89A641C587C05EDE590B3FF98D9F89C0746054ED8DBC3C0C9E8",
    ),
    "system/product/app/KeKePay/KeKePay.apk": (
        "walletfix_phb_components/KeKePay/KeKePay.apk",
        "047BA6537C8C41620C94845F4BCBC51D5952D5E5E3FC1384DF961D10EFC357D4",
    ),
    "system/product/app/FinShellWallet/FinShellWallet.apk": (
        "wallet/FinShellWallet/FinShellWallet.apk",
        "7E7D27FF6407D052219762F07822D313401DED53E907382A23CFC1364920BEA7",
    ),
    "system/product/app/UPTsmService/UPTsmService.apk": (
        "tsm/UPTsmService/UPTsmService.apk",
        "6ADA3A9F3AC0E91B4D499DC60509B5E12DFC351076A12A17C0B158E0ECAD56C2",
    ),
}
EID_FILES = {
    "odm/bin/hw/vendor.oplus.hardware.eid@1.0-service": (
        "eid_phb110/bin/hw/vendor.oplus.hardware.eid@1.0-service",
        "D529DCFD38C526AC848A93673994C44CA9B6A5F7C29B8400FAD8F92351735A5F",
    ),
    "odm/etc/vintf/manifest/manifest_oplus_eid.xml": (
        "eid_phb110/etc/vintf/manifest/manifest_oplus_eid.xml",
        "0AF56438D42D68F694CF502E5F4FB9F72F6EC4B320FBAEA4B495A192E3287DD3",
    ),
    "odm/lib/vendor.oplus.hardware.eid-V1-ndk.so": (
        "eid_phb110/lib/vendor.oplus.hardware.eid-V1-ndk.so",
        "B0F2A2D8B6701DB897444A889C4EFDEA3822B2EA3A5F34C9B465ED2ED18B3997",
    ),
    "odm/lib64/vendor.oplus.hardware.eid-V1-ndk.so": (
        "eid_phb110/lib64/vendor.oplus.hardware.eid-V1-ndk.so",
        "5F4F4806AE4A2ABD89C2B4A419B183939523241EA12172A73BE255567FA459DD",
    ),
}
EID_ORIGINAL_RC = (
    "eid_phb110/etc/init/vendor.oplus.hardware.eid@1.0-service.rc",
    "C3B116B2CF95B3F558CEDEE4B4FD03E3B8EF46F55823E8618AE2FC03F9AF2142",
)
REPLACED_DIRS = (
    "system/product/priv-app/KeKeUserCenter/",
    "system/product/priv-app/KeKeUserCenterAccount/",
    "system/product/priv-app/OpenID/",
    "system/product/app/TasWallet/",
    "system/product/app/KeKePay/",
    "system/product/app/FinShellWallet/",
    "system/product/app/UPTsmService/",
)

INSTALL_GUARD = '''if [ "$(getprop ro.product.model)" != "CPH2449" ] || [ "$(getprop ro.build.version.release)" != "16" ]; then
  abort "! PHB110 module requires CPH2449 on Android 16"
fi
if [ -e /data/adb/walletfix/spoof_vars ] && [ "$(cat /data/adb/walletfix/spoof_vars)" != "MODEL=PHB110" ]; then
  abort "! Existing walletfix spoof_vars differs; back it up and resolve the conflict first"
fi

'''
CONFIG_SETUP = '''if [ ! -e /data/adb/walletfix/spoof_vars ]; then
  mkdir -p /data/adb/walletfix || abort "! Cannot create walletfix config directory"
  printf 'MODEL=PHB110\\n' > /data/adb/walletfix/spoof_vars || abort "! Cannot write walletfix config"
  : > "$MODPATH/.created_spoof_vars"
fi

'''
UNINSTALL = '''MODDIR=${0%/*}
if [ -f "$MODDIR/.created_spoof_vars" ] && [ "$(cat /data/adb/walletfix/spoof_vars 2>/dev/null)" = "MODEL=PHB110" ]; then
  rm -f /data/adb/walletfix/spoof_vars
  rmdir /data/adb/walletfix 2>/dev/null || true
fi
'''
PRIVAPP_PERMISSIONS = '''<?xml version="1.0" encoding="utf-8"?>
<permissions>
    <privapp-permissions package="com.heytap.vip">
        <permission name="android.permission.READ_PRIVILEGED_PHONE_STATE" />
        <permission name="android.permission.GET_ACCOUNTS_PRIVILEGED" />
    </privapp-permissions>
    <privapp-permissions package="com.oplus.account">
        <permission name="android.permission.READ_PRIVILEGED_PHONE_STATE" />
        <permission name="android.permission.GET_ACCOUNTS_PRIVILEGED" />
    </privapp-permissions>
    <privapp-permissions package="com.heytap.openid">
        <permission name="android.permission.INTERACT_ACROSS_USERS" />
    </privapp-permissions>
</permissions>
'''
EID_INITRC = '''# PHB110 eID service, registered by KernelSU before Android init parses services.
service eid-1-0 /odm/bin/hw/vendor.oplus.hardware.eid@1.0-service
    class hal
    user system
    group system
    interface aidl vendor.oplus.hardware.eid.IEidDevice/default
    disabled

# Hybrid Mount mounts odm after init parses rc; start only after that mount.
on property:sys.boot_completed=1
    start eid-1-0
'''
EID_SERVICE = '''MODDIR=${0%/*}
LOG_FILE="$MODDIR/eid-service.log"

# One fallback start after the overlay is mounted, if the init trigger missed it.
while [ "$(getprop sys.boot_completed)" != "1" ]; do
    sleep 2
done
state=$(getprop init.svc.eid-1-0)
if [ "$state" != "running" ] && [ -n "$state" ]; then
    setprop ctl.start eid-1-0
    state=$(getprop init.svc.eid-1-0)
fi
printf 'eid-1-0 state: %s\n' "${state:-not registered}" > "$LOG_FILE"
'''
EID_INSTALL = '''ui_print "- Extracting PHB110 eID HAL and init registration"
extract "$ZIPFILE" 'initrc/eid.rc' "$MODPATH"
for file in $(unzip -l "$ZIPFILE" | awk '{print $4}' | grep '^odm/' | grep -v '/$' | grep -v '\\.sha256$'); do
  extract "$ZIPFILE" "$file" "$MODPATH"
done
set_perm_recursive "$MODPATH/odm" 0 0 0755 0644 u:object_r:vendor_file:s0
set_perm_recursive "$MODPATH/odm/bin" 0 0 0755 0755 u:object_r:vendor_file:s0
set_perm "$MODPATH/odm/bin/hw/vendor.oplus.hardware.eid@1.0-service" 0 2000 0755 u:object_r:hal_eid_oplus_exec:s0
set_perm_recursive "$MODPATH/odm/etc" 0 0 0755 0644 u:object_r:vendor_configs_file:s0

'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require_hash(path: Path, expected: str) -> None:
    if not path.is_file():
        raise ValueError(f"Missing ROM file: {path}")
    actual = sha256(path)
    if actual != expected:
        raise ValueError(f"Wrong SHA-256 for {path}: {actual}; expected {expected}")


def replace_once(data: str, old: str, new: str) -> str:
    if data.count(old) != 1:
        raise ValueError(f"Unexpected upstream installer layout near: {old}")
    return data.replace(old, new, 1)


def patched_installer(source: str, with_eid: bool = False) -> str:
    guard = INSTALL_GUARD
    if with_eid:
        guard += 'if [ -z "$KSU" ]; then\n  abort "! PHB110 eID requires KernelSU initrc injection"\nfi\n\n'
    source = replace_once(source, 'VERSION=$(grep_prop version "${TMPDIR}/module.prop")',
                          guard + 'VERSION=$(grep_prop version "${TMPDIR}/module.prop")')
    source = replace_once(source, 'extract "$ZIPFILE" \'post-fs-data.sh\' "$MODPATH"',
                          'extract "$ZIPFILE" \'post-fs-data.sh\' "$MODPATH"\n'
                          'extract "$ZIPFILE" \'system.prop\' "$MODPATH"\n'
                          'extract "$ZIPFILE" \'uninstall.sh\' "$MODPATH"')
    source = replace_once(source, 'mv "$TMPDIR/sepolicy.rule" "$MODPATH"',
                          'mv "$TMPDIR/sepolicy.rule" "$MODPATH"\n\n' + CONFIG_SETUP)
    if with_eid:
        source = replace_once(source, 'HAS32BIT=false &&', EID_INSTALL + 'HAS32BIT=false &&')
    return source


def zip_info(name: str, executable: bool = False) -> ZipInfo:
    info = ZipInfo(name)
    info.create_system = 3
    info.external_attr = ((0o100755 if executable else 0o100644) << 16)
    info.compress_type = ZIP_DEFLATED
    return info


def add_file(archive: ZipFile, name: str, data: bytes, *, executable: bool = False) -> None:
    archive.writestr(zip_info(name, executable), data)
    archive.writestr(zip_info(name + ".sha256"), hashlib.sha256(data).hexdigest().encode())


def component_files(rom_root: Path):
    for target, (relative, expected) in COMPONENTS.items():
        apk = rom_root / relative
        require_hash(apk, expected)
        source_dir = apk.parent
        target_dir = target.rsplit("/", 1)[0]
        for source in sorted(source_dir.rglob("*")):
            if not source.is_file() or "oat" in source.relative_to(source_dir).parts:
                continue
            if source.suffix in (".vdex", ".odex", ".art"):
                continue
            yield f"{target_dir}/{source.relative_to(source_dir).as_posix()}", source


def build(base_zip: Path, rom_root: Path, output_dir: Path, with_eid: bool = False) -> Path:
    require_hash(base_zip, BASE_SHA256)
    files = list(component_files(rom_root))
    if with_eid:
        require_hash(rom_root / EID_ORIGINAL_RC[0], EID_ORIGINAL_RC[1])
        for target, (relative, expected) in EID_FILES.items():
            source = rom_root / relative
            require_hash(source, expected)
            files.append((target, source))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ("WalletFix4OOS-PHB110-eID.zip" if with_eid else "WalletFix4OOS-PHB110.zip")
    temporary = output.with_suffix(".zip.tmp")

    with ZipFile(base_zip) as upstream, ZipFile(temporary, "w") as candidate:
        old_installer = upstream.read("customize.sh").decode()
        installer = patched_installer(old_installer, with_eid)
        module = upstream.read("module.prop").decode()
        module = "\n".join(line for line in module.splitlines() if not line.startswith("updateJson=")) + "\n"
        module = replace_once(module, "name=Wallet Fix for OxygenOS",
                              "name=Wallet Fix for OxygenOS PHB110")
        module = replace_once(module, "version=2.3.0 (1064-8d00352-release)",
                              "version=2.3.0-PHB110.2")
        module = replace_once(module, "versionCode=1064", "versionCode=1065")
        module = replace_once(module, "description=Fix Oneplus Wallet for OxygenOS 14/15",
                              "description=CPH2449 OxygenOS 16 wallet adaptation from PHB110 ROM")
        if with_eid:
            module = replace_once(module, "name=Wallet Fix for OxygenOS PHB110",
                                  "name=Wallet Fix for OxygenOS PHB110 eID")
            module = replace_once(module, "version=2.3.0-PHB110.2",
                                  "version=2.3.0-PHB110.2-eID")
        changed = {
            "customize.sh": installer.encode(),
            "module.prop": module.encode(),
        }
        if with_eid:
            changed["service.sh"] = EID_SERVICE.encode()
        for item in upstream.infolist():
            name = item.filename
            if any(name.startswith(prefix) for prefix in REPLACED_DIRS):
                continue
            if name in changed or name in {key + ".sha256" for key in changed}:
                continue
            candidate.writestr(item, upstream.read(name))
        for name, data in changed.items():
            add_file(candidate, name, data, executable=name.endswith(".sh"))
        add_file(candidate, "system.prop", b"ro.product.cuptsm=ONEPLUS|ESE|01|02\n")
        add_file(candidate, "uninstall.sh", UNINSTALL.encode(), executable=True)
        if with_eid:
            add_file(candidate, "initrc/eid.rc", EID_INITRC.encode())
        add_file(candidate,
                 "system/product/etc/permissions/privapp-permissions-walletfix-phb110.xml",
                 PRIVAPP_PERMISSIONS.encode())
        for name, source in files:
            add_file(candidate, name, source.read_bytes())

    temporary.replace(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-zip", required=True, type=Path)
    parser.add_argument("--rom-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--with-eid", action="store_true",
                        help="include the PHB110 eID HAL and KernelSU init registration")
    args = parser.parse_args()
    try:
        result = build(args.base_zip, args.rom_root, args.output_dir, args.with_eid)
    except (ValueError, OSError, KeyError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    print(f"Built {result}")
    print("The phone was not modified. Wallet and TSM apps are included in the module ZIP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
