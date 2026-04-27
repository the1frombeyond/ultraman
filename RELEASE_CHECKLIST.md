# ULTRAMAN v1.0.0 Release Checklist

## Pre-Release Checklist

### Code
- [x] main.py - Zero-config bootstrap
- [x] install.py - Full installer with CLI registration
- [x] ultraman.cmd - Windows launcher
- [x] ultraman.sh - Unix launcher
- [x] build.py - PyInstaller build script

### Documentation
- [x] README.md - User-facing landing page
- [ ] LICENSE - MIT license file
- [ ] CONTRIBUTING.md - Contribution guidelines

### Testing
- [ ] Test install.py on clean Windows system
- [ ] Test install.py on clean Linux system
- [ ] Test CLI command registration
- [ ] Test main.py first-run flow
- [ ] Test chat loop functionality

### Build Artifacts
- [ ] ULTRAMAN.exe built via PyInstaller
- [ ] Exe tested on Windows

## Release Steps

### 1. Version Bump
```bash
# Update VERSION in:
# - install.py
# - main.py (if referenced)
# - setup/config files
```

### 2. Git Tag
```bash
git tag -a v1.0.0 -m "ULTRAMAN v1.0.0 - Initial Public Release"
git push origin v1.0.0
```

### 3. Create GitHub Release
- Title: `ULTRAMAN v1.0.0`
- Attach: ULTRAMAN.exe
- Body: Copy README.md highlights

### 4. Announce
- Share release link
- Document installation issues

---

## File Manifest for v1.0.0

```
ULTRAMAN/
├── main.py              # Entry point (includes bootstrap)
├── install.py          # Installer
├── ultraman.cmd        # Windows CLI
├── ultraman.sh        # Unix CLI
├── build.py           # Build script
├── README.md          # Documentation
├── requirements.txt   # Dependencies
├── ultraman/
│   ├── core/          # AI engine
│   ├── ui/           # Interface
│   └── ...
└── skills/           # Skill modules
```

---

## Post-Release

- Monitor GitHub issues
- Collect user feedback
- Track installation success rate
- Plan v1.1.0 features