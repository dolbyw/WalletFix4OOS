# OnePlus 11 PHB110 adaptation

Target: CPH2449 running OxygenOS 16, with KernelSU, Zygisk Next, and a system-file metamodule. The source ROM is PHB110 ColorOS 16.0.5.701. The device is not modified by the build process.

The official 2.3.0 module already supplies Zygisk code that changes `Build.MODEL` only in `com.finshell.wallet` and `com.unionpay.tsmservice`. This adaptation keeps that binary, configures it with `MODEL=PHB110`, and replaces all five bundled OnePlus 12 applications with the corresponding OnePlus 11 ROM files: `KeKeUserCenter`, `KeKeUserCenterAccount`, `OpenID`, `TasWallet`, and `KeKePay`. The wallet and UnionPay TSM APKs remain separate installation files, following upstream's design. Precompiled ART files are omitted because they belong to the donor ROM.

The module adds the PHB110 ROM's `ro.product.cuptsm=ONEPLUS|ESE|01|02` through KernelSU `system.prop` and a narrow product privapp allowlist for the three account packages. It does not change NFC routing, vendor/odm images, Google Wallet, or any bank app. Its installer refuses other device models or Android releases and refuses to overwrite an existing incompatible spoof configuration. The module removes only a spoof configuration it created itself on uninstall.

This is a buildable candidate, not proof of working login, card provisioning, or eSE access. Those require controlled on-device testing and logs after separate user authorization.
