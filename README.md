# Wallet Fix for OnePlus 11 (CPH2449)

适配目标：一加 11 CPH2449、OxygenOS 16.0.5.702(EX01)、KernelSU + Zygisk Next + Hybrid Mount。国行组件取自同机型 PHB110 ColorOS 16.0.5.701(CN01) 全量 ROM。

**状态：基础包和可选 eID 包已完成本地构建与 ZIP 校验；均未安装到手机。账号登录、工牌、交通卡和 eID 尚需真机验证。**

## 模块内容

- 用 PHB110 的账号中心、OpenID、TasWallet、KeKePay 替换上游一加 12 组件。覆盖海外 `KeKeUserCenter` 目录来切换账号服务。
- 沿用上游 Zygisk 库，仅在钱包和银联 TSM 进程内设 `Build.MODEL=PHB110`；已有不同内容的 `/data/adb/walletfix/spoof_vars` 会使安装中止。
- 通过 KernelSU `system.prop` 设置国行 ROM 原值 `ro.product.cuptsm=ONEPLUS|ESE|01|02`，加入账号组件所需的 product privapp 权限。仅允许在 CPH2449 / Android 16 安装。
- 可选 eID 版本额外覆盖 PHB110 的 `/odm` eID 可执行文件、两份接口库和 VINTF 声明，并通过 KernelSU `initrc` 在启动早期注册服务、开机完成后启动。OOS 已有的 `com.oplus.eid` 服务 APK 的代码和清单与 PHB110 相同，无须替换。SELinux eID 域和主要依赖库在 OOS 中也已存在。
- 不直接写入 `/vendor`、`/odm` 或更改 NFC 路由文件。停用模块并重启可撤销账号、属性及可选 eID 覆盖。

本仓库不上传国行 APK。构建脚本校验上游 2.3.0 release ZIP 和 PHB110 ROM APK 的 SHA-256，输出模块 ZIP 及单独安装的钱包、银联 TSM APK。上游项目：[geniucker-dev/WalletFix4OOS](https://github.com/geniucker-dev/WalletFix4OOS)。

## 本地构建和测试

工作空间中已有 ROM 提取结果；在本仓库根目录运行：

```powershell
$python='C:\Users\husk1\AppData\Roaming\uv\python\cpython-3.12.16-windows-x86_64-none\python.exe'
$base='D:\Projects\movewallet\tools\Wallet-Fix-for-OxygenOS-2.3.0-1064-8d00352-release.zip'
$rom='D:\Projects\movewallet\rom-extracted'
& $python scripts\build_phb110.py --base-zip $base --rom-root $rom --output-dir 'D:\Projects\movewallet\WalletFix4OOS\dist'
& $python scripts\build_phb110.py --base-zip $base --rom-root $rom --output-dir 'D:\Projects\movewallet\WalletFix4OOS\dist' --with-eid
$env:PHB110_BASE_ZIP=$base
$env:PHB110_ROM_ROOT=$rom
& $python -m unittest discover -s tests -v
```

输出：基础包 `dist/WalletFix4OOS-PHB110.zip`、可选包 `dist/WalletFix4OOS-PHB110-eID.zip`，以及单独安装的 `FinShellWallet.apk`、`UPTsmService.apk`。两个模块包 ID 相同，一次只安装一个；eID 包要求 KernelSU 的 `initrc` 注入功能。`dist/` 不会提交到 Git。

## 工作流程

1. 构建脚本核对上游 release ZIP 和 PHB110 ROM 文件的 SHA-256，再把同机型账号组件、权限 XML 与 `system.prop` 封进模块；钱包和银联 TSM APK 单独输出。eID 包另外核对并封入同机型 HAL。
2. 安装器核对 CPH2449 / Android 16，解压并逐个校验文件哈希，覆盖海外账号中心。KernelSU 借助 Hybrid Mount 挂载模块文件，并从 `system.prop` 加载国行 `ro.product.cuptsm`。
3. Zygisk 只在钱包及银联 TSM 相关进程内映射机型为 PHB110，让国行组件按同机型路径工作；不做全局机型伪装。钱包、账号中心、TSM 与 NFC/eSE 随后各自完成应用和卡片流程。
4. eID 包由 KernelSU 在 Android init 解析配置时注册 `eid-1-0`；挂载完成后启动 PHB110 eID HAL，供手机已有的 `com.oplus.eid` 调用。Android init 正常管理这个服务，模块仅在服务未运行时做一次启动补救。

此流程仍需真机验证。上游 eID 试验曾有注册失败和相机异常报告，因此先测试基础包，确认钱包、相机、Google 钱包与银行 App，再选择是否测试 eID 包。

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

要测试 eID，先安装基础包并确认基本功能，再用 KernelSU 安装同 ID 的 `WalletFix4OOS-PHB110-eID.zip` 并重启。确认 `getprop init.svc.eid-1-0` 为 `running`、`service list` 中有 `vendor.oplus.hardware.eid.IEidDevice/default`，再在钱包里验证 eID；同时复查相机。服务启动只说明 HAL 已注册，不等于 eID 开通或认证成功。

```powershell
& $adb -s 2d842a6c shell su -c '/data/adb/ksud module disable walletfix4oos'
& $adb -s 2d842a6c reboot
```

## 待真机确认

- eID HAL 已纳入可选包，但注册、开通和认证尚未实测；若安装后相机异常或启动失败，禁用模块并重启，再换回基础包。
- 国行账号、eSE 和工牌录入仍可能受服务端或卡片类型限制，需真机日志确认。

许可证：[GPL-3.0](LICENSE)。
