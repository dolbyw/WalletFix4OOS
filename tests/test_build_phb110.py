import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_APKS = {
    "system/product/priv-app/KeKeUserCenter/KeKeUserCenter.apk": "56E65CDA7DAB732A514A04A3832B93E721D6526C2E81080FC1B6E9FAF0943E81",
    "system/product/priv-app/KeKeUserCenterAccount/KeKeUserCenterAccount.apk": "780321D251A8A178251E8F169FF0133C64922D7C7A017B07E5EC6B68B4F35ACC",
    "system/product/priv-app/OpenID/OpenID.apk": "5E79220E6E3838B5E1FBCA6C86CE0BB069321773A578D43D9CCEC9B57A1A9AC4",
    "system/product/app/TasWallet/TasWallet.apk": "E7CA8CA5542BC89A641C587C05EDE590B3FF98D9F89C0746054ED8DBC3C0C9E8",
    "system/product/app/KeKePay/KeKePay.apk": "047BA6537C8C41620C94845F4BCBC51D5952D5E5E3FC1384DF961D10EFC357D4",
    "system/product/app/FinShellWallet/FinShellWallet.apk": "7E7D27FF6407D052219762F07822D313401DED53E907382A23CFC1364920BEA7",
    "system/product/app/UPTsmService/UPTsmService.apk": "6ADA3A9F3AC0E91B4D499DC60509B5E12DFC351076A12A17C0B158E0ECAD56C2",
}


class BuildPhb110Test(unittest.TestCase):
    def test_build_uses_only_phb110_components(self):
        base = os.environ.get("PHB110_BASE_ZIP")
        rom = os.environ.get("PHB110_ROM_ROOT")
        if not base or not rom:
            self.skipTest("Set PHB110_BASE_ZIP and PHB110_ROM_ROOT for ROM-backed integration test")

        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_phb110.py"),
                 "--base-zip", base, "--rom-root", rom, "--output-dir", tmp],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            package = Path(tmp) / "WalletFix4OOS-PHB110.zip"
            self.assertTrue(package.is_file())
            with ZipFile(package) as archive:
                names = set(archive.namelist())
                self.assertFalse(any(n.endswith((".vdex", ".odex", ".art")) for n in names))
                for name, expected in EXPECTED_APKS.items():
                    self.assertIn(name, names)
                    actual = hashlib.sha256(archive.read(name)).hexdigest().upper()
                    self.assertEqual(actual, expected, name)
                    self.assertEqual(archive.read(name + ".sha256").decode(), expected.lower())
                self.assertEqual(archive.read("system.prop").decode().strip(),
                                 "ro.product.cuptsm=ONEPLUS|ESE|01|02")
                installer = archive.read("customize.sh").decode()
                self.assertIn("CPH2449", installer)
                self.assertIn("ro.build.version.release", installer)
                self.assertIn("MODEL=PHB110", installer)
                self.assertIn("spoof_vars", installer)
                self.assertIn("uninstall.sh", names)
                self.assertNotIn("initrc/eid.rc", names)
                self.assertFalse(any(n.startswith(("system/odm/", "odm/")) for n in names))
                self.assertIn("system/product/app/FinShellWallet/lib/arm64/libeidjni.so", names)
                self.assertIn("system/product/app/UPTsmService/lib/arm64/libuptsmservice.so", names)
                self.assertIn("system/product/etc/permissions/privapp-permissions-walletfix-phb110.xml", names)
                module = archive.read("module.prop").decode()
                self.assertIn("id=walletfix4oos", module)
                self.assertIn("version=2.3.0-PHB110.2", module)
                self.assertIn("versionCode=1065", module)
                self.assertNotIn("updateJson=", module)

            self.assertFalse((Path(tmp) / "FinShellWallet.apk").exists())
            self.assertFalse((Path(tmp) / "UPTsmService.apk").exists())

    def test_eid_variant_contains_phb110_hal_and_init_registration(self):
        base = os.environ.get("PHB110_BASE_ZIP")
        rom = os.environ.get("PHB110_ROM_ROOT")
        if not base or not rom:
            self.skipTest("Set PHB110_BASE_ZIP and PHB110_ROM_ROOT for ROM-backed integration test")

        expected = {
            "odm/bin/hw/vendor.oplus.hardware.eid@1.0-service": "D529DCFD38C526AC848A93673994C44CA9B6A5F7C29B8400FAD8F92351735A5F",
            "odm/etc/vintf/manifest/manifest_oplus_eid.xml": "0AF56438D42D68F694CF502E5F4FB9F72F6EC4B320FBAEA4B495A192E3287DD3",
            "odm/lib/vendor.oplus.hardware.eid-V1-ndk.so": "B0F2A2D8B6701DB897444A889C4EFDEA3822B2EA3A5F34C9B465ED2ED18B3997",
            "odm/lib64/vendor.oplus.hardware.eid-V1-ndk.so": "5F4F4806AE4A2ABD89C2B4A419B183939523241EA12172A73BE255567FA459DD",
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build_phb110.py"),
                 "--base-zip", base, "--rom-root", rom, "--output-dir", tmp, "--with-eid"],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            package = Path(tmp) / "WalletFix4OOS-PHB110-eID.zip"
            with ZipFile(package) as archive:
                names = set(archive.namelist())
                for name, digest in expected.items():
                    self.assertIn(name, names)
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest().upper(), digest)
                self.assertNotIn("odm/etc/init/vendor.oplus.hardware.eid@1.0-service.rc", names)
                self.assertFalse(any(n.startswith("system/odm/") for n in names))
                init = archive.read("initrc/eid.rc").decode()
                self.assertIn("service eid-1-0 /odm/bin/hw/vendor.oplus.hardware.eid@1.0-service", init)
                self.assertIn("interface aidl vendor.oplus.hardware.eid.IEidDevice/default", init)
                self.assertIn("on property:sys.boot_completed=1", init)
                installer = archive.read("customize.sh").decode()
                self.assertIn("initrc/eid.rc", installer)
                self.assertIn("PHB110 eID requires KernelSU initrc injection", installer)
                self.assertIn("hal_eid_oplus_exec", installer)
                self.assertIn("vendor_configs_file", installer)
                service = archive.read("service.sh").decode()
                self.assertIn("ctl.start eid-1-0", service)
                self.assertNotIn("MAX_RETRIES=10", service)
                self.assertIn("PHB110 eID", archive.read("module.prop").decode())

    def test_source_bundle_contains_required_apps_and_eid_files(self):
        rom = os.environ.get("PHB110_ROM_ROOT")
        if not rom:
            self.skipTest("Set PHB110_ROM_ROOT for ROM-backed integration test")
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "PHB110-components.zip"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "package_phb110_sources.py"),
                 "--rom-root", rom, "--output", str(package)],
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with ZipFile(package) as archive:
                names = set(archive.namelist())
                self.assertIn("wallet/FinShellWallet/FinShellWallet.apk", names)
                self.assertIn("wallet/FinShellWallet/lib/arm64/libeidjni.so", names)
                self.assertIn("tsm/UPTsmService/UPTsmService.apk", names)
                self.assertIn("eid_phb110/bin/hw/vendor.oplus.hardware.eid@1.0-service", names)
                self.assertFalse(any(n.endswith((".vdex", ".odex", ".art")) for n in names))
                for line in archive.read("SHA256SUMS.txt").decode().splitlines():
                    digest, path = line.split("  ", 1)
                    self.assertEqual(hashlib.sha256(archive.read(path)).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
