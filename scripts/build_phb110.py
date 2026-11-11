#!/usr/bin/env python3
"""Build a private CPH2449 module from the official 2.3.0 ZIP and PHB110 ROM files."""

import argparse
import hashlib
from pathlib import Path
import shutil
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
}
EXTRA_APKS = {
    "FinShellWallet.apk": (
        "wallet/FinShellWallet/FinShellWallet.apk",
        "7E7D27FF6407D052219762F07822D313401DED53E907382A23CFC1364920BEA7",
    ),
    "UPTsmService.apk": (
        "tsm/UPTsmService/UPTsmService.apk",
        "6ADA3A9F3AC0E91B4D499DC60509B5E12DFC351076A12A17C0B158E0ECAD56C2",
    ),
}
REPLACED_DIRS = (
    "system/product/priv-app/KeKeUserCenter/",
    "system/product/priv-app/KeKeUserCenterAccount/",
    "system/product/priv-app/OpenID/",
    "system/product/app/TasWallet/",
    "system/product/app/KeKePay/",
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


def patched_installer(source: str) -> str:
    source = replace_once(source, 'VERSION=$(grep_prop version "${TMPDIR}/module.prop")',
                          INSTALL_GUARD + 'VERSION=$(grep_prop version "${TMPDIR}/module.prop")')
    source = replace_once(source, 'extract "$ZIPFILE" \'post-fs-data.sh\' "$MODPATH"',
                          'extract "$ZIPFILE" \'post-fs-data.sh\' "$MODPATH"\n'
                          'extract "$ZIPFILE" \'system.prop\' "$MODPATH"\n'
                          'extract "$ZIPFILE" \'uninstall.sh\' "$MODPATH"')
    source = replace_once(source, 'mv "$TMPDIR/sepolicy.rule" "$MODPATH"',
                          'mv "$TMPDIR/sepolicy.rule" "$MODPATH"\n\n' + CONFIG_SETUP)
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


def build(base_zip: Path, rom_root: Path, output_dir: Path) -> Path:
    require_hash(base_zip, BASE_SHA256)
    for relative, expected in EXTRA_APKS.values():
        require_hash(rom_root / relative, expected)
    files = list(component_files(rom_root))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "WalletFix4OOS-PHB110.zip"
    temporary = output.with_suffix(".zip.tmp")

    with ZipFile(base_zip) as upstream, ZipFile(temporary, "w") as candidate:
        old_installer = upstream.read("customize.sh").decode()
        installer = patched_installer(old_installer)
        module = upstream.read("module.prop").decode()
        module = "\n".join(line for line in module.splitlines() if not line.startswith("updateJson=")) + "\n"
        module = replace_once(module, "name=Wallet Fix for OxygenOS",
                              "name=Wallet Fix for OxygenOS PHB110")
        module = replace_once(module, "version=2.3.0 (1064-8d00352-release)",
                              "version=2.3.0-PHB110.1")
        module = replace_once(module, "description=Fix Oneplus Wallet for OxygenOS 14/15",
                              "description=CPH2449 OxygenOS 16 wallet adaptation from PHB110 ROM")
        changed = {
            "customize.sh": installer.encode(),
            "module.prop": module.encode(),
        }
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
        add_file(candidate,
                 "system/product/etc/permissions/privapp-permissions-walletfix-phb110.xml",
                 PRIVAPP_PERMISSIONS.encode())
        for name, source in files:
            add_file(candidate, name, source.read_bytes())

    temporary.replace(output)
    for name, (relative, _) in EXTRA_APKS.items():
        shutil.copyfile(rom_root / relative, output_dir / name)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-zip", required=True, type=Path)
    parser.add_argument("--rom-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.base_zip, args.rom_root, args.output_dir)
    except (ValueError, OSError, KeyError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    print(f"Built {result}")
    print("The phone was not modified. Wallet and TSM APKs are separate output files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
