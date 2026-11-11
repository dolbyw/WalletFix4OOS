# Wallet Fix for OnePlus 11 (CPH2449)

适配目标：一加 11 CPH2449、OxygenOS 16.0.5.702(EX01)、KernelSU + Zygisk Next + Hybrid Mount。国行组件取自同机型 PHB110 ColorOS 16.0.5.701(CN01) 全量 ROM。

**状态：基础包和可选 eID 包已完成本地构建与 ZIP 校验；均未安装到手机。账号登录、工牌、交通卡和 eID 尚需真机验证。**

## 模块内容

- 用 PHB110 的账号中心、OpenID、TasWallet、KeKePay 替换上游一加 12 组件。覆盖海外 `KeKeUserCenter` 目录来切换账号服务。钱包 `com.finshell.wallet` 和银联 TSM `com.unionpay.tsmservice` 连同 native 库也封入模块，挂载为普通 product 系统 App。
- 沿用上游 Zygisk 库，仅在钱包和银联 TSM 进程内设 `Build.MODEL=PHB110`；已有不同内容的 `/data/adb/walletfix/spoof_vars` 会使安装中止。
- 通过 KernelSU `system.prop` 设置国行 ROM 原值 `ro.product.cuptsm=ONEPLUS|ESE|01|02`，加入账号组件所需的 product privapp 权限。仅允许在 CPH2449 / Android 16 安装。
- 可选 eID 版本额外从模块顶层 `odm/` 覆盖 PHB110 的 `/odm` eID 可执行文件、两份接口库和 VINTF 声明，并通过 KernelSU `initrc` 在启动早期注册服务、开机完成后启动。这台 OOS 没有 `/system/odm` 链接，因此 Hybrid Mount 需要模块顶层 `odm/`。OOS 已有的 `com.oplus.eid` 服务 APK 的代码和清单与 PHB110 相同，无须替换。SELinux eID 域和主要依赖库在 OOS 中也已存在。
- 不直接写入 `/vendor`、`/odm` 或更改 NFC 路由文件。停用模块并重启可撤销账号、属性及可选 eID 覆盖。

代码仓库保持精简。所需国行 APK、native 库和 eID 文件打包为 `PHB110-components.zip`，与可直接刷入的两个模块 ZIP 一起放在 [GitHub Release](https://github.com/dolbyw/WalletFix4OOS/releases/tag/phb110-0.2.0)。这些国行文件属于各自权利人，不受本仓库 GPL 许可证覆盖。构建脚本校验上游 release 和关键国行文件的 SHA-256。上游项目：[geniucker-dev/WalletFix4OOS](https://github.com/geniucker-dev/WalletFix4OOS)。

发布文件 SHA-256：组件包 `3C4A86232C7BEA8FC163A7493B01403E2387318F9955E0DD78AE09E7A06B253F`；基础模块 `B1A65CF03F1E9C8DFDC2239017787E8D471FE4A5C72F4EF63DCDA61993E13EE8`；eID 模块 `EED667F50FFFE898365B582B2D36C0DEEFAFA62F043FF841AB54AB0457B2B8C2`。

## 手机上安装

从 Release 下载 `WalletFix4OOS-PHB110.zip`，在 KernelSU 的模块页面选择本地安装并重启。钱包与银联 TSM 会随模块挂载，无须另外安装 APK。先验证账号、钱包、工牌、相机、Google 钱包和银行 App；确认基础功能后，才用同一模块 ID 的 `WalletFix4OOS-PHB110-eID.zip` 更新并重启测试 eID。两种 ZIP 不要同时安装。

## 本地构建和测试

从 Release 下载 `PHB110-components.zip` 并解压，另从[上游 2.3.0 发布页](https://github.com/geniucker-dev/WalletFix4OOS/releases/tag/2.3.0)取得 release ZIP；在本仓库根目录运行：

```powershell
$python='C:\Users\husk1\AppData\Roaming\uv\python\cpython-3.12.16-windows-x86_64-none\python.exe'
$base='D:\Projects\movewallet\tools\Wallet-Fix-for-OxygenOS-2.3.0-1064-8d00352-release.zip'
$rom='D:\Projects\movewallet\WalletFix4OOS\dist\phb110-input'
Expand-Archive -LiteralPath 'D:\Projects\movewallet\WalletFix4OOS\dist\PHB110-components.zip' -DestinationPath $rom -Force
& $python scripts\build_phb110.py --base-zip $base --rom-root $rom --output-dir 'D:\Projects\movewallet\WalletFix4OOS\dist'
& $python scripts\build_phb110.py --base-zip $base --rom-root $rom --output-dir 'D:\Projects\movewallet\WalletFix4OOS\dist' --with-eid
$env:PHB110_BASE_ZIP=$base
$env:PHB110_ROM_ROOT=$rom
& $python -m unittest discover -s tests -v
```

输出：基础包 `dist/WalletFix4OOS-PHB110.zip` 和可选包 `dist/WalletFix4OOS-PHB110-eID.zip`。两包都包含钱包与银联 TSM；eID 包要求 KernelSU 的 `initrc` 注入功能。`dist/` 不会提交到 Git。若已从完整 ROM 提取文件，也可用 `scripts/package_phb110_sources.py` 重新生成组件包。

## 工作流程

1. 构建脚本核对上游 release ZIP 和 PHB110 组件文件的 SHA-256，再把同机型账号组件、钱包、银联 TSM、native 库、权限 XML 与 `system.prop` 封进模块。eID 包另外封入同机型 HAL。
2. 安装器核对 CPH2449 / Android 16，解压并逐个校验文件哈希，覆盖海外账号中心。KernelSU 借助 Hybrid Mount 挂载模块文件，并从 `system.prop` 加载国行 `ro.product.cuptsm`。
3. Zygisk 只在钱包及银联 TSM 相关进程内映射机型为 PHB110，让国行组件按同机型路径工作；不做全局机型伪装。钱包、账号中心、TSM 与 NFC/eSE 随后各自完成应用和卡片流程。
4. eID 包由 KernelSU 在 Android init 解析配置时注册 `eid-1-0`；挂载完成后启动 PHB110 eID HAL，供手机已有的 `com.oplus.eid` 调用。Android init 正常管理这个服务，模块仅在服务未运行时做一次启动补救。

此流程仍需真机验证。上游 eID 试验曾有注册失败和相机异常报告，因此先测试基础包，确认钱包、相机、Google 钱包与银行 App，再选择是否测试 eID 包。

## 真机测试与回滚

**以下命令会改动手机，目前未执行。** 也可按前述步骤在手机 KernelSU 中安装。模块会切换账号组件，实际使用前应备份重要账号与卡片数据。指定序列号避免操作另一台 ADB 设备。

```powershell
$adb='D:\Green\platform-tools\adb.exe'
& $adb -s 2d842a6c push 'D:\Projects\movewallet\WalletFix4OOS\dist\WalletFix4OOS-PHB110.zip' /data/local/tmp/WalletFix4OOS-PHB110.zip
& $adb -s 2d842a6c shell su -c '/data/adb/ksud module install /data/local/tmp/WalletFix4OOS-PHB110.zip'
& $adb -s 2d842a6c reboot
```

重启后核对 `getprop ro.product.cuptsm`、`pm list packages com.oplus.account`、`pm list packages com.finshell.wallet` 和 `pm list packages com.unionpay.tsmservice`，再实际验证登录、录卡、Google 钱包与银行 App。若有问题，先禁用模块并重启；卡片数据是否保留取决于 App 与服务端状态，不要直接清除应用数据。

要测试 eID，先安装基础包并确认基本功能，再用 KernelSU 安装同 ID 的 `WalletFix4OOS-PHB110-eID.zip` 并重启。确认 `getprop init.svc.eid-1-0` 为 `running`、`service list` 中有 `vendor.oplus.hardware.eid.IEidDevice/default`，再在钱包里验证 eID；同时复查相机。服务启动只说明 HAL 已注册，不等于 eID 开通或认证成功。

```powershell
& $adb -s 2d842a6c shell su -c '/data/adb/ksud module disable walletfix4oos'
& $adb -s 2d842a6c reboot
```

## 待真机确认

- eID HAL 已纳入可选包，但注册、开通和认证尚未实测；若安装后相机异常或启动失败，禁用模块并重启，再换回基础包。
- 国行账号、eSE 和工牌录入仍可能受服务端或卡片类型限制，需真机日志确认。

许可证：[GPL-3.0](LICENSE)。
