# PulseRing Super V2.8.1 — APK Source Recovery / APK 原始碼復原

> **Status / 狀態：PARTIAL RECOVERY TOOLKIT — not a fully decompiled or verified buildable Android project.**  
> **目前交付的是 APK 逆向分析與 Windows 自動反編譯工具包，不是已通過編譯的完整原始碼。**

## 繁體中文

### 這份工具包從什麼來？

這是使用者自行提供、聲稱由使用者與 ChatGPT 共同開發的 `PulseRing Super V2.8.1.apk`。本工具包只檢查 APK 靜態結構，不執行 APK、不連線至戒指、不收集手機資料。

已確認 APK 包含 `com.conner.fixfate` 應用程式、三個 DEX、AndroidManifest、資源檔及 AndroidX 原生元件。靜態類別清單可辨識約 303 個第一方類別，原始 Kotlin 檔案名稱線索包含 `GreenfieldRingRepository.kt`、`AndroidBleTransport.kt`、`YcbtFrameCodec.kt`、`LocalMetricStore.kt`、`SleepEvidenceEvaluator.kt` 與 Compose UI 畫面。**這不代表原始 Kotlin 原始碼已由本工具包還原。**

### 實際使用的技術（從 APK 類別名稱與封裝資訊確認）

- Android / Kotlin 編譯程式（DEX 中的 `.kt` SourceFile 註記）
- Jetpack Compose（UI 套件與依賴類別）
- Android Bluetooth Low Energy（BLE）傳輸、GATT 通訊類別
- Kotlin Coroutines、Flow（封裝依賴）
- 自有 YCBT 協定解析、歷史資料、度量輪詢程式模組
- 背景監控服務、Android foreground services
- 本地健康資料儲存、睡眠資料解析及視覺化相關類別

上述為靜態程式架構觀察，**不是這些功能已通過真實戒指測試的證明**。

### Windows 還原操作

1. 將整個 ZIP 解壓到任意資料夾，保留 `PRIVATE_INPUT/PulseRing Super V2.8.1.apk`。
2. 安裝 **Java JDK 11 或更新版本**，確認 PowerShell 中 `java -version` 可執行。
3. 以 PowerShell 進入解壓後資料夾，執行：

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Recover-on-Windows.ps1
   ```

4. 腳本會從 [JADX 官方 GitHub 發布頁](https://github.com/skylot/jadx/releases) 下載 JADX 1.5.6，以一般 CLI 模式執行 APK 反編譯。
5. **`WORK_DECOMPILED_NOT_FOR_GITHUB/`：** 所有反編譯結果，包含第三方相依套件，請留在本機。
6. **`GITHUB_REVIEW_BEFORE_PUSH/`：** 僅選取 `com.conner.fixfate` 程式碼與資源供你逐項檢查。此資料夾不是保證可編譯的 Android Studio 原始專案。
7. 如果掃描出潛在金鑰，腳本會停止。即使沒掃到也必須人工確認所有檔案，再決定是否公開。

### 還原限制

反編譯無法可靠還原原始 Kotlin 註解、變數名稱、Gradle 設定、簽章資訊及完整原始碼版本。編譯器產生的 synthetic 類別和 Compose 結構也可能與原始碼差異很大。若要得到真正可維護的 Kotlin 專案，仍需從原 Android Studio 專案復原，或進行**人工重建與編譯測試**。本回合無法在容器取得 JADX 執行檔，所以沒有宣稱已完成全部 Java 方法反編譯。

### GitHub 公開安全規則

- **切勿直接上傳這份 ZIP**：其中的 `PRIVATE_INPUT` 含原始 APK，可能有不宜公開的內容。
- 建議只上傳審查後、真正擁有授權的第一方程式碼。不要把 AndroidX、Kotlin、Google、其他 SDK 的反編譯程式碼當成自己作品。
- 不可公開真實 Token、API Key、BLE 裝置識別資訊、健康讀數、私人紀錄、語音素材。
- 此工具包沒有代你選擇開源授權。請先確認授權後再加入 LICENSE。
- 執行 `git status`、秘密掃描與人工檢視後才提交；**腳本不會自動 push**。

## English

### Overview

This package analyzes an APK provided by the developer and prepares a reproducible **JADX source-recovery workflow** for Windows. The app ID found in DEX/manifest metadata is `com.conner.fixfate`.

Static inspection identified three DEX files and approximately 303 first-party application classes. Android code indicates Kotlin, Jetpack Compose, BLE/GATT transport, Coroutines/Flow, YCBT packet/history parsing, metric storage, and background monitoring. These observations **do not establish runtime correctness**.

### Run on Windows

1. Extract the ZIP (including the `PRIVATE_INPUT` folder).
2. Install Java 11+ and confirm `java -version` works.
3. Run: `powershell -NoProfile -ExecutionPolicy Bypass -File .\Recover-on-Windows.ps1`
4. The script downloads official JADX 1.5.6 and runs standard CLI decompilation, generating:
   - `WORK_DECOMPILED_NOT_FOR_GITHUB/`: **private, complete JADX extraction**.
   - `GITHUB_REVIEW_BEFORE_PUSH/`: first-party source candidates and decoded resources for manual review.

### Limitations and publication checks

APK decompilation generally yields approximate Java, **not the original Kotlin source or a verified Android Studio project**. Decompiled methods, resource mappings, and generated Gradle configuration may require manual work before the app builds. The source files have **not** been compiled or tested in this package.

Review for credentials, personal data, copyrighted third-party source, and licenses before publishing. Do not upload the bundled APK or private working folder. The script does not create a Git repository or push to GitHub.

### Validation

This toolkit is based on offline ZIP/DEX structural parsing. Counts, SHA-256 and first-party class names are documented under `analysis/`. No full JADX run or APK rebuild has been performed in this environment.
