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
                self.assertIn("system/product/etc/permissions/privapp-permissions-walletfix-phb110.xml", names)
                module = archive.read("module.prop").decode()
                self.assertIn("id=walletfix4oos", module)
                self.assertNotIn("updateJson=", module)

            for name, digest in {
                "FinShellWallet.apk": "7E7D27FF6407D052219762F07822D313401DED53E907382A23CFC1364920BEA7",
                "UPTsmService.apk": "6ADA3A9F3AC0E91B4D499DC60509B5E12DFC351076A12A17C0B158E0ECAD56C2",
            }.items():
                self.assertEqual(hashlib.sha256((Path(tmp) / name).read_bytes()).hexdigest().upper(), digest)


if __name__ == "__main__":
    unittest.main()
