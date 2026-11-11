## WalletFix4OOS 更新日志

### 2.3.0-PHB110.3 (1066)

适配一加 11 CPH2449 / OxygenOS 16.0.5.702（PHB110 ColorOS 16.0.5.701 组件）。由 ChatGPT 与 DeepSeek 完成适配与真机排障。

fix:
- 模块 App「屡次停止运行」：模块挂载在 App 进程命名空间里被 `kernel_umount` 摘掉，APK ENOENT，绑定期 `GraphicsEnvironment.queryAngleChoice` NPE
- 账号中心 `Resources$NotFoundException`：不再覆盖 `/product/priv-app/KeKeUserCenter`（CN 的 `com.heytap.vip` 壳会破坏 OEM `com.oneplus.account`）
- 点「登录」后账号 App `ExceptionInInitializerError`：钱包按 `Build.BRAND` 拼 accountType，伪装 `BRAND/MANUFACTURER=OPPO` 后改走国行账号中心 `com.oplus.account`
- 卡包「充值」一直转圈：随账号登录打通（`signup-info` 返回 SUC）

changes:
- `service.sh` 开机自动维护 `/data/adb/walletfix/spoof_vars`（补 `BRAND`/`MANUFACTURER`）与 Hybrid Mount `disable_umount`
- 安装器不再要求 `spoof_vars` 内容完全一致，只要求含 `MODEL=PHB110`
- `uninstall.sh` 正确还原 Hybrid Mount 配置

### 2.3.0

feature:
- Support custom target apps list via `/data/adb/walletfix/target.txt`

### 2.2.4

fix:
- Support OxygenOS 16

changes:
- update apps from OnePlus 12 ColorOS PJD110_16.0.0.201(CN01) F.33

> **If OxygenOS 15 does not work, please use the previous version 2.2.3**
> **如果OxygenOS 15无法使用，请使用上一个版本2.2.3**

### 2.2.3

- update apps from OnePlus 12 ColorOS PJD110_15.0.0.860(CN01) C.82

### 2.2.2

- update apps from OnePlus 12 ColorOS PJD110_15.0.0.832(CN01) C.79

### 2.2.1

- fix: compatibility with KernelSU Next

### 2.2.0

- Add 2 new related apps.

> **If you update from 2.0.1 or earlier, please uninstall the old version first.**
> **如果您从2.0.1或更早版本更新，请先卸载旧版本。**

### 2.1.0

- fix: default config is not loaded
- fix: free unused memory
- perf: use embeded default config instead the file in module folder to decrease file read
- refine code

> **If you update from 2.0.1 or earlier, please uninstall the old version first.**
> **如果您从2.0.1或更早版本更新，请先卸载旧版本。**

### 2.0.2

- rename id to `walletfix4oos`
- update from OnePlus 12 ColorOS PJD110_15.0.0.206(CN01) C.56

> **If you update from 2.0.1 or earlier, please uninstall the old version first.**
> **如果您从2.0.1或更早版本更新，请先卸载旧版本。**

### 2.0.1

- fix: spoof MODEL to all Oneplus Wallet process and unionpay tsmservice
- log: refine logging

### 2.0.0

- Use zygisk to spoof MODEL only to Oneplus Wallet (instead of global spoofing)
- update apps from OnePlus 12 ColorOS PJD110_14.0.0.860(CN01) A.79

### 1.0.1

Nothing changed.

### 1.0.0

- update from OnePlus 12 ColorOS PJD110_14.0.0.840(CN01) A.77
