# Wallet Fix for OnePlus 11 (CPH2449)

适配目标：一加 11 CPH2449、OxygenOS 16.0.5.702(EX01)、KernelSU + Zygisk Next + Hybrid Mount。国行组件取自同机型 PHB110 ColorOS 16.0.5.701(CN01) 全量 ROM。

**状态：本地构建与 ZIP 校验已完成；尚未在手机上验证账号登录、工牌、交通卡。eID 未适配。**

## 模块内容

- 用 PHB110 的账号中心、OpenID、TasWallet、KeKePay 替换上游一加 12 组件。覆盖海外 `KeKeUserCenter` 目录来切换账号服务。
- 沿用上游 Zygisk 库，仅在钱包和银联 TSM 进程内设 `Build.MODEL=PHB110`；已有不同内容的 `/data/adb/walletfix/spoof_vars` 会使安装中止。
- 通过 KernelSU `system.prop` 设置国行 ROM 原值 `ro.product.cuptsm=ONEPLUS|ESE|01|02`，加入账号组件所需的 product privapp 权限。仅允许在 CPH2449 / Android 16 安装。
- 不修改 `/vendor`、`/odm` 或 NFC 路由文件。停用模块并重启可撤销账号覆盖与属性。

本仓库不上传国行 APK。构建脚本校验上游 2.3.0 release ZIP 和 PHB110 ROM APK 的 SHA-256，输出模块 ZIP 及单独安装的钱包、银联 TSM APK。上游项目：[geniucker-dev/WalletFix4OOS](https://github.com/geniucker-dev/WalletFix4OOS)。

## 本地构建和测试

工作空间中已有 ROM 提取结果；在本仓库根目录运行：

```powershell
$python='C:\Users\husk1\AppData\Roaming\uv\python\cpython-3.12.16-windows-x86_64-none\python.exe'
$base='D:\Projects\movewallet\tools\Wallet-Fix-for-OxygenOS-2.3.0-1064-8d00352-release.zip'
$rom='D:\Projects\movewallet\rom-extracted'
& $python scripts\build_phb110.py --base-zip $base --rom-root $rom --output-dir 'D:\Projects\movewallet\WalletFix4OOS\dist'
$env:PHB110_BASE_ZIP=$base
$env:PHB110_ROM_ROOT=$rom
& $python -m unittest discover -s tests -v
```

输出：`dist/WalletFix4OOS-PHB110.zip`、`dist/FinShellWallet.apk`、`dist/UPTsmService.apk`。`dist/` 不会提交到 Git。

## 真机测试与回滚

**以下命令会改动手机，目前未执行。** 模块会切换账号组件，实际使用前应备份重要账号与卡片数据。指定序列号避免操作另一台 ADB 设备。

```powershell
$adb='D:\Green\platform-tools\adb.exe'
& $adb -s 2d842a6c install -r 'D:\Projects\movewallet\WalletFix4OOS\dist\FinShellWallet.apk'
& $adb -s 2d842a6c install -r 'D:\Projects\movewallet\WalletFix4OOS\dist\UPTsmService.apk'
& $adb -s 2d842a6c push 'D:\Projects\movewallet\WalletFix4OOS\dist\WalletFix4OOS-PHB110.zip' /data/local/tmp/WalletFix4OOS-PHB110.zip
& $adb -s 2d842a6c shell su -c '/data/adb/ksud module install /data/local/tmp/WalletFix4OOS-PHB110.zip'
& $adb -s 2d842a6c reboot
```

重启后核对 `getprop ro.product.cuptsm`、`pm list packages com.oplus.account` 和 `pm list packages com.finshell.wallet`，再实际验证登录、录卡、Google 钱包与银行 App。若有问题，先禁用模块并重启；钱包及 TSM 用户 App 会保留，避免直接删除卡片数据。

```powershell
& $adb -s 2d842a6c shell su -c '/data/adb/ksud module disable walletfix4oos'
& $adb -s 2d842a6c reboot
```

## 未解决

- eID：未加入 PHB110 eID HAL，也未做真机验证。
- 国行账号、eSE 和工牌录入仍可能受服务端或卡片类型限制，需真机日志确认。

许可证：[GPL-3.0](LICENSE)。
