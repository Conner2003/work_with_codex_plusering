# PulseRing Super V2.8.1

**Independent Android BLE companion app and protocol-research project for the Future Lab FIX FATE PulseRing**  
**Future Lab FIX FATE PulseRing 智慧戒指｜Android BLE 獨立開發與通訊協定研究專案**

> **Project status / 專案狀態:** Experimental, device-specific research. The available release artifact is an APK; the original buildable Android Studio source project has **not** been recovered or verified from that APK.  
> **研究狀態：** 目前可檢查的正式產物是 APK；**尚未**從 APK 驗證還原出原始、可重新編譯的 Android Studio 專案。本文記錄實際逆向研究過程、已確認的封包證據、程式架構與限制。

- **App package:** `com.conner.fixfate`
- **Analyzed build:** `PulseRing Super V2.8.1.apk`
- **APK SHA-256:** `dd914f09d326870e51bfcc523bafc8dd766de66ea15aa9c7489ba3a30ad7e6e3`
- **Reference device:** Future Lab FIX FATE PulseRing; `FG16504` is a **retail size/SKU identifier**, **not** a proven BLE chipset or firmware identifier.
- **Development approach:** Independent development with ChatGPT-assisted investigation, Android BLE testing, controlled HCI packet capture, firmware-protocol comparison, and iterative real-device experiments.

**Language / 語言:** [繁體中文](#繁體中文) · [English](#english)

---

## 繁體中文

### 1. 專案介紹

PulseRing Super 是我與 ChatGPT 協作研究、針對自己持有的 Future Lab FIX FATE 智慧戒指開發的**非官方 Android Companion App**。目標是在不依賴原廠 App 日常操作的情況下，探索戒指的 BLE GATT 服務、解讀標準與專有封包，並在 Android 上管理量測、歷史紀錄及背景資料收集。

這不是對原廠功能的 100% 還原保證，也不是聲稱取得了戒指的韌體原始碼。我以**實際手機↔戒指通訊紀錄**、反向分析、程式實作與逐版本測試，逐步確認各功能是否真的可運作。

### 2. 使用技術與架構

| 技術 | 用途 | 證據範圍 |
|---|---|---|
| **Android / Kotlin** | Android App 核心程式與業務邏輯 | V2.8.1 APK 內含 `.kt` SourceFile 線索及第一方類別 |
| **Jetpack Compose** | 原生宣告式 UI、健康數據頁面 | APK 的 UI 類別與相依套件 |
| **Android Bluetooth LE / GATT** | 掃描、連線、Service Discovery、Characteristic Read/Write、Notification/Indication | 程式類別與早期真機 HCI 測試 |
| **Bluetooth HCI snoop + ADB + Wireshark/封包解析** | 記錄我自己的 Android 裝置與戒指交換的 BLE HCI/ATT 資料，重建通訊時間線 | 先前實際擷取與 TSV 統計 |
| **Kotlin Coroutines / Flow** | 非同步連線狀態、資料事件與 UI 更新 | APK 靜態程式／相依套件 |
| **YCBT / BE94 proprietary protocol research** | 解析廠商專有命令、回覆、歷史記錄與電量 | OEM APK 研究及真機封包對照；非官方完整規格 |
| **本地資料儲存與分析** | 量測資料、歷史紀錄、趨勢與睡眠相關處理 | APK 中辨識出的模組；臨床準確性未驗證 |
| **Android Foreground Service** | 背景監控與連線維持 | APK 程式結構；實際省電行為依手機而異 |
| **JADX / DEX 靜態分析** | 檢視發行 APK 的類別結構；輔助重建原始碼線索 | Source Recovery Kit；未完成完整反編譯／重建 |

V2.8.1 APK 中可辨識的第一方原始檔名線索包括：

```text
AndroidBleTransport.kt       GreenfieldRingRepository.kt
RingTransport.kt             RingRepository.kt
YcbtCommands.kt              YcbtFrameCodec.kt
YcbtFrameAssembler.kt        YcbtHistoryParser.kt
YcbtHistoryTransfer.kt       MetricPollingPolicy.kt
StandardHeartRateDecoder.kt  LocalMetricStore.kt
SleepEvidenceEvaluator.kt    RingMonitorService.kt
RingCompanionService.kt      HomeScreen.kt
HealthHistoryChart.kt        SleepScreen.kt
```

> 以上僅代表從 APK 的 DEX 中辨識出類別與原始檔名線索，**不代表這些原始 Kotlin 檔案已被還原**；亦不等於每個功能都通過真機驗收。

### 3. 我如何擷取／分析戒指封包

#### 3.1 擷取的範圍

我使用自己持有的 Android 手機與智慧戒指進行受控測試，透過 Android **Developer options → Enable Bluetooth HCI snoop log** 記錄手機藍牙控制器的 HCI 事件。這是**本機 HCI 擷取**，不是攔截其他人的藍牙通訊，也不是宣稱已破解空中加密。

研究流程：

1. 在 Android 開啟開發者選項及 Bluetooth HCI snoop 記錄；依裝置要求重新啟動藍牙或重新開機。
2. 先以原廠 App 連線、觸發量測／查詢／歷史同步等操作，建立**已知行為對照樣本**；另以自製 App 重複相同測試，避免兩個 App 同時搶連線。
3. 在 Windows 電腦使用 **ADB** 取得自己的 Android 裝置診斷資料，例如：

   ```powershell
   adb devices
   adb bugreport pulsering-bugreport.zip
   ```

4. 從 bugreport 或裝置提供的藍牙診斷位置找出 `btsnoop_hci.log`（**不同 Android 版本／廠商可能放在不同路徑，也可能限制存取**），再使用 Wireshark 或自製解析腳本分析 ATT/GATT 事件。
5. 依時間順序關聯 **Service Discovery → CCCD 訂閱 → TX Write → Write Callback → RX Notify/Indicate**，整理成 TSV，計數、分析時距與回覆命令。
6. 將原廠 App 的操作與封包、以及自製 App 的指令／回覆交叉比對，只把**能重複觀察到的現象**作為協定實作依據。

可在 Wireshark 使用 `btatt` 檢視 ATT 封包；封包屬於特定連線與 Handle，必須先透過該次 Service Discovery 將 Handle 對應到特徵 UUID，**不能把一次擷取的 Handle 當成永久固定值**。

#### 3.2 實際封包證據（V2.4.0 階段的一次樣本）

一份已分析的約 **353.91 秒**擷取紀錄包含 **473 筆**事件：

| 類型 | 筆數 |
|---|---:|
| GATT／Discovery 事件 | 14 |
| TX | 50 |
| Write callbacks（回覆狀態 0） | 50 |
| RX 合計 | 357 |
| └ 標準心率 `0x2A37` | 337 |
| └ 專有 `BE940003` | 20 |

該次樣本中，`BE940001` 和 `AE02` **沒有 RX 事件**。這不代表它們在其他韌體或後續測試中永遠不會回覆。

心率 `0x2A37` 通知的第一個 Flags byte 皆觀察到 `0x04`，且沒有 RR-Interval 欄位：**337 筆中有 196 筆心率值為 0，141 筆非 0**。通知約每秒一次；**通知頻率不等於有效心率量測頻率**，也不應把心率 0 當成真正的 0 BPM 生理數值。

#### 3.3 觀察到的 GATT 通道

| UUID／特徵（縮寫） | 研究用途 | 注意事項 |
|---|---|---|
| `0x180D / 0x2A37` | 標準 Heart Rate Measurement Notify | 真機驗證存在；Flags 與資料有效性須解析 |
| `BE940001` | 專有 Write / Write Without Response / Indicate 能力（依 Discovery） | 通道屬性與實際訂閱／收包是不同概念 |
| `BE940002` | 專有寫入側通道（在部分研究樣本觀察） | 不能假設所有韌體相同 |
| `BE940003` | 專有 Indicate 回覆／事件 | V2.4.0 樣本有 20 筆 RX |
| `AE02` | 另一專有 Notify 通道 | V2.4.0 App 測試未訂閱／未收到；其他擷取條件不同 |
| `0x180F` | 標準 Battery Service | 早期 GATT 探查**未觀察到**，不代表裝置沒有電量資料 |

**重要：** 裝置 SKU `FG16504` 不可當成韌體平台識別碼；BE94/AE 通道對照與裝置韌體版本有關，請以每次 GATT Discovery 結果為準。

#### 3.4 專有封包與命令研究

分析原廠 Android APK 中的 Yucheng `com.yucheng.ycbtsdk` 線索，並與實際 HCI 交易比較後，研究中採用的 YCBT 封包模型為：

```text
[CMD_H][CMD_L][LEN_L][LEN_H][PAYLOAD...][CRC_LO][CRC_HI]
```

解析時需處理 **little-endian 的長度與 CRC 欄位**、CRC16（研究樣本使用 `0xFFFF` 初始值）、不完整封包的緩衝組裝、回覆命令比對，以及 BLE Write 與 Notify/Indicate 的非同步順序。**這是研究所得的通道／封包模型，不宣稱是所有 FIX FATE 型號的官方完整協定。**

部分後續研究曾記錄 `0x0200` 的電量相關回覆，以及 `0x05xx` 歷史資料查詢／回覆配對；命令意義必須依實際裝置封包、資料欄位與可重現測試進一步確認，不能僅因某次回傳數字看似合理就宣稱已完整解碼。

### 4. 如何從研究走向自製 App

```text
OWN DEVICE / 自有戒指
  │
  ├─ Official App baseline / 原廠 App 操作對照
  │        └─ Android HCI snoop → ATT/GATT trace → TSV 分析
  │
  └─ PulseRing Super
           ├─ BLE scan / connect / discover
           ├─ Subscribe Notify / Indicate (CCCD)
           ├─ Write command → wait for correlated reply
           ├─ Frame assembly / CRC / command parser
           ├─ Standard 0x2A37 heart-rate decoding
           ├─ Proprietary metric/history probes
           ├─ Local storage / time-series UI
           └─ Background foreground-service monitoring
```

工程上特別關注以下事項：

- **連線狀態機：** Scan、Connect、Discover、Subscribe、Ready、Disconnect、Reconnect 都要有明確狀態與錯誤恢復；Android Scan error `1` 可能是已在掃描，不宜直接判定裝置不存在。
- **交易與排程：** 不同度量查詢需要處理 Busy、timeout、write callback、對應 response、重試與冷卻時間；避免某一類指令占住佇列，導致其他資料長期收不到。
- **數據品質：** 原始 payload、解析結果、時間戳、樣本可信度分開保存；有數值不等於已證明它是血氧、HRV 或睡眠分期。
- **Android 背景限制：** Foreground Service、通知與 BLE 權限需依 OS 版本實作；低耗電及關閉 UI 後持續收集都需真機驗證。
- **資料安全：** 本地健康記錄、BLE 識別碼、HCI 記錄、Google 登入設定／其他密鑰不得原樣公開。

### 5. 已觀察到的成果與尚未證實的部分

**有證據支持的研究里程碑：** BLE 連線與標準心率通知；多次原廠／自製 App 封包擷取與 UUID 探查；專有命令的寫入與部分回覆；在後續 V2.5.x 測試中，使用者回報曾取得電量、血氧候選值、體表溫度候選值及 HRV 候選值。

**不應宣稱已驗證：** 所有候選量測的準確性、壓力值有可靠的直接來源、REM／深睡／淺睡的臨床級判讀、任意版本韌體的相容性、全天候穩定背景監控，或 V2.8.1 所有功能的端到端 PASS。不同版本的封包測試結果不可直接當成 V2.8.1 的重新測試結果。

### 6. GitHub 發布與原始碼還原

目前能直接檢查的 V2.8.1 產物是 APK：3 個 DEX、約 303 個第一方類別候選，以及許多第三方套件。利用 **JADX** 可取得近似 Java 的反編譯結果，**不能保證還原原始 Kotlin、註解、Gradle 依賴、簽章或完整可編譯專案**。

若搭配先前的 Source Recovery Kit，在 Windows 11 上可於解壓後執行：

```powershell
java -version
powershell -NoProfile -ExecutionPolicy Bypass -File .\Recover-on-Windows.ps1
```

**公開前必做：** 移除 APK／私人 HCI 原始記錄／個人健康資料／API Key／Token／簽章私鑰；確認自己擁有公開每份檔案的權利。**不可直接把反編譯的原廠 SDK 或其他第三方程式當成自己的開源作品。** 開源授權應由權利人確認後另外選定；尚未提供明確授權時，不要自行宣稱 MIT/Apache-2.0。

### 7. 聲明

本專案為**非官方、獨立的互通性與技術研究**，並非 Future Lab、FIX FATE、Yucheng 或其他廠商的官方產品或背書。所討論的封包擷取只針對研究者自己的手機和裝置。本 App 及研究性健康數據**不得作為醫療診斷或治療依據**。

---

## English

### 1. About this project

PulseRing Super is an **unofficial Android BLE companion-app and interoperability research project** developed through collaboration between the developer and ChatGPT for the developer's own Future Lab FIX FATE smart ring. The goal is to explore GATT services, correlate standard and proprietary messages with real device behavior, and implement an independent Android app for readings, history, and background monitoring.

This is **not** a claim of access to the ring's firmware source, a fully decoded vendor protocol, clinical-grade measurements, or complete feature parity with the OEM application.

### 2. Technical stack

| Technology | Role | Evidence / qualification |
|---|---|---|
| **Android + Kotlin** | App logic and transport | `.kt` SourceFile hints and first-party classes in V2.8.1 DEX |
| **Jetpack Compose** | Declarative Android UI | APK code/dependency inspection |
| **Android Bluetooth Low Energy / GATT** | Scan, connect, service discovery, characteristic I/O, notifications/indications | App modules plus earlier hardware traces |
| **Bluetooth HCI snoop, ADB, Wireshark, TSV analysis** | Record and correlate the developer's own HCI/ATT traffic | Observed capture workflow and traces |
| **Kotlin Coroutines / Flow** | Asynchronous connection state and data streams | APK dependency inspection |
| **YCBT / proprietary BE94 protocol research** | Command framing, vendor responses, history queries | OEM APK analysis plus real-device observations |
| **Local metrics / charts / sleep-related modules** | Store and display measurements | Static app class evidence; not a medical accuracy claim |
| **Android foreground monitoring** | Background BLE activity | App architecture; actual reliability unverified here |
| **JADX / DEX inspection** | APK source-recovery investigation | Structural analysis, not a rebuilt source project |

Identified first-party Kotlin filename clues include `AndroidBleTransport.kt`, `GreenfieldRingRepository.kt`, `YcbtFrameCodec.kt`, `YcbtFrameAssembler.kt`, `MetricPollingPolicy.kt`, `LocalMetricStore.kt`, `SleepEvidenceEvaluator.kt`, and `RingMonitorService.kt`. These names were recovered as **metadata hints**, not verified original Kotlin source files.

### 3. How I captured and analyzed the BLE packets

I tested a **ring and Android handset I own**. On Android, I enabled **Developer options → Enable Bluetooth HCI snoop log**, then reproduced operations with the OEM app and with PulseRing Super in separate sessions. This is **host-controller traffic logging on my own phone**, not over-the-air interception of third-party traffic or a Bluetooth encryption bypass.

A reproducible high-level workflow:

1. Enable HCI snoop logging; restart Bluetooth or the device if needed.
2. Connect the OEM app, perform one identifiable operation at a time (connect, read metric, request history), and disconnect. Repeat using the independent app. Do not let both apps compete for the GATT connection.
3. Collect a device bugreport with Android Debug Bridge (ADB):

   ```powershell
   adb devices
   adb bugreport pulsering-bugreport.zip
   ```

4. Locate the `btsnoop_hci.log` in the bugreport or another device-specific Bluetooth diagnostics location, when accessible. Its location and availability depend on Android build and device policy.
5. In Wireshark, inspect ATT traffic (for example, display filter `btatt`) and correlate each handle to that session's discovered characteristic UUIDs.
6. Correlate **service discovery → CCCD writes → characteristic TX → write callbacks → characteristic notifications / indications**, and export an event timeline to TSV for counts, timing, and command-response analysis.
7. Compare recorded behavior against OEM app usage and independent replay. Treat hypotheses as unconfirmed until supported by repeated traces.

#### Real captured evidence (one V2.4.0-era trace)

A **353.91-second** trace contained **473 events**: 14 GATT/discovery events, 50 TX events, 50 write callbacks, and 357 RX events. Of those RX events, **337** were standard heart-rate characteristic `0x2A37` notifications, and **20** were vendor `BE940003` messages. There were **no incoming `BE940001` or `AE02` messages in that particular trace**—this is a sample-specific statement, not proof the channels are never used.

The `0x2A37` payloads in that trace carried Flags `0x04` and no RR-interval fields; **196 / 337** decoded to a zero heart-rate value and **141 / 337** to nonzero values. Notifications were seen roughly once per second. **Notification frequency is not equivalent to valid heart-rate sampling frequency**, and a zero payload must not automatically be treated as a physiological reading of 0 BPM.

#### GATT characteristics observed during research

| Characteristic / service | Observed role | Caveat |
|---|---|---|
| `0x180D / 0x2A37` | Standard Heart Rate Service / Measurement Notify | Validate flags and meaningful payload |
| `BE940001` | Vendor write/write-without-response/indicate-capable characteristic | Discovered capability ≠ actual RX subscription |
| `BE940002` | Vendor write-side characteristic in some traces | Firmware/version dependent |
| `BE940003` | Vendor indication channel | 20 incoming messages in the noted trace |
| `AE02` | Alternative vendor notify path | Not subscribed / not receiving in that run; other runs differ |
| `0x180F` | Standard Battery Service | Not found during an earlier discovery; vendor battery data can still exist |

The retail identifier `FG16504` is **not verified as a chipset or firmware ID**. Do not hardcode session-specific ATT handles or assume the same proprietary UUID usage across every model.

#### Protocol framing and decoding

Research of the OEM app's `com.yucheng.ycbtsdk` package and corresponding HCI transactions produced the following **working YCBT frame model**:

```text
[CMD_H][CMD_L][LEN_L][LEN_H][PAYLOAD...][CRC_LO][CRC_HI]
```

The investigation involved little-endian length/CRC fields, CRC16 with an observed initialization value of `0xFFFF`, fragmented-frame assembly, request/response correlation, and timeouts. Some later experiments observed battery-related responses to `0x0200` and mappings among `0x05xx` history commands. These observations do **not** constitute a full official protocol specification; payload interpretation must be validated per device/firmware.

### 4. Independent development approach

```text
Own FIX FATE ring
  ├── OEM-app controlled experiments
  │      └── HCI snoop → ATT/GATT traces → TSV evidence
  └── PulseRing Super for Android
         ├── BLE scan/connect/discover/reconnect
         ├── CCCD setup for notify/indicate
         ├── Asynchronous write and response tracking
         ├── Vendor frame assembly, CRC, command parsing
         ├── Standard heart-rate characteristic decoding
         ├── Proprietary metric and history probes
         ├── Local samples, trends, and UI
         └── Foreground-service background monitoring
```

Key lessons:

- **Explicit connection state machine:** scan, connect, discover, subscribe, ready, disconnect, reconnect, and error handling. Android BLE scan error `1` can mean an already-started scan, not necessarily a missing ring.
- **Serialized / correlated transactions:** handle callbacks, indication acknowledgements, timeouts, retries, and cool-downs without starving other metrics.
- **Separate raw vs. interpreted data:** keep payload, timestamp, decoder version, confidence/quality flag, and derived metric distinct.
- **Respect Android background restrictions:** BLE and foreground-service permissions and battery optimizations vary across Android versions.
- **Protect user data:** do not upload real HCI captures, device identifiers, health history, private keys, or authentication material to public repositories.

### 5. What was observed vs. what remains unverified

**Observed in previous development iterations:** device BLE connection; standard heart-rate notifications; service/characteristic discovery; proprietary writes and some replies; user-reported battery, SpO₂ candidate, skin-temperature candidate and HRV candidate readings in later V2.5.x tests.

**Not established:** clinical accuracy of those derived measurements, an independently validated stress metric, medically valid REM/deep/light sleep staging, universal firmware compatibility, reliably persistent low-power background collection, or an end-to-end verification of all V2.8.1 features. Results from an earlier app version are not a substitute for retesting V2.8.1.

### 6. Source recovery, building, and open-source publication

The supplied V2.8.1 artifact is an APK with **three DEX files** and approximately **303 candidate first-party classes**, alongside third-party libraries. **Decompiling an APK yields approximate Java, not necessarily the original Kotlin sources, Gradle project, signing keys, or reproducible build.** A buildable Android Studio source tree has not been verified.

If using the separate recovery kit on Windows 11:

```powershell
java -version
powershell -NoProfile -ExecutionPolicy Bypass -File .\Recover-on-Windows.ps1
```

The script targets a JADX-based offline decompilation workflow. **Do not publish the raw APK/recovery-kit bundle or vendor SDK source by default.** Public repositories should contain only reviewed first-party code and appropriately licensed dependencies, with all credentials, device identifiers, health data, raw private captures, and signing material removed. A public software license should be selected by the actual rights holder after review; none is implicitly granted by this README.

### 7. Disclaimer

This is an **unofficial independent research and interoperability project**, not endorsed by Future Lab, FIX FATE, Yucheng, or any OEM. Packet-capture instructions concern only hardware and accounts owned or explicitly authorized by the researcher. Experimental readings and sleep interpretation are **not for medical diagnosis or treatment**.
