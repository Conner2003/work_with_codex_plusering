# GitHub 發布前檢查 / Publication Checklist

This APK recovery kit is PRIVATE; **do not upload this whole kit** to GitHub.

## Checkpoints

- [ ] Successfully ran `Recover-on-Windows.ps1` and reviewed Java decompilation warnings.
- [ ] Manually verified that `GITHUB_REVIEW_BEFORE_PUSH/` contains **only files you are permitted to publish**.
- [ ] Removed test credentials, API keys, device MAC addresses, health records, user identifiers and local logs.
- [ ] Removed/attributed third-party source and assets; all required libraries are declared as external dependencies.
- [ ] Added actual build configuration and verified whether an Android Studio build succeeds. If it does not, keep the "non-buildable recovered source" warning.
- [ ] Added a license only after confirming ownership and third-party terms.
- [ ] Prepared a clear README describing what works, what is unverified, and limitations of APK reconstruction.
- [ ] Checked `.gitignore` and `git status` and conducted a secret scan before the initial commit.

## After all checks are completed

Open PowerShell from **`GITHUB_REVIEW_BEFORE_PUSH/`**, not the recovery ZIP root:

```powershell
git init -b main
git add .
git status
git diff --cached --stat
# Review what is staged before you commit.
git commit -m "Publish reviewed PulseRing Super recovered source"
git remote add origin https://github.com/YOUR_ACCOUNT/PulseRing-Super.git
git push -u origin main
```

Use a newly created **empty repository** under your own GitHub account. Change `YOUR_ACCOUNT` to the actual GitHub username; this is an example, not an existing URL. If any push protection alert appears, **remove the secret from the affected commits** and revoke/rotate exposed credentials — never bypass the alert just to finish uploading.

**Do not describe the decompiled Java as the original Kotlin project** unless you have verified exact provenance.
