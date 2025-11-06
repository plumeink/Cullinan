# Build Scripts Guide

Cullinan provides powerful build scripts to package your web applications into standalone executables.

## Available Scripts

### 1. `build_app.py` - Universal Builder (Recommended)

**Auto-detecting, interactive build script that works with both Nuitka and PyInstaller.**

```bash
# Interactive mode (recommended for beginners)
python scripts/build_app.py

# Quick builds
python scripts/build_app.py --tool nuitka          # Use Nuitka
python scripts/build_app.py --tool pyinstaller     # Use PyInstaller
python scripts/build_app.py --mode onefile         # Single file output

# Custom entry point
python scripts/build_app.py --entry your_app/main.py --tool nuitka
```

**Features:**
- ✅ Auto-detects entry point
- ✅ Auto-discovers packages
- ✅ Interactive tool selection
- ✅ Supports both Nuitka and PyInstaller
- ✅ Cross-platform

---

### 2. `build_nuitka_advanced.py` - Advanced Nuitka Builder

**Full-featured Nuitka build script with compiler selection and optimization.**

```bash
# Basic builds
python scripts/build_nuitka_advanced.py                    # Standalone
python scripts/build_nuitka_advanced.py --onefile          # Single file

# Compiler selection
python scripts/build_nuitka_advanced.py --compiler gcc     # Use GCC
python scripts/build_nuitka_advanced.py --compiler mingw64 # Use MinGW64
python scripts/build_nuitka_advanced.py --compiler msvc    # Use MSVC
python scripts/build_nuitka_advanced.py --compiler clang   # Use Clang

# Optimized builds
python scripts/build_nuitka_advanced.py --optimize         # Enable LTO
python scripts/build_nuitka_advanced.py --onefile --optimize

# With icon
python scripts/build_nuitka_advanced.py --icon app.ico
python scripts/build_nuitka_advanced.py --onefile --icon app.ico --no-console
```

**Features:**
- ✅ GCC/MSVC/Clang/MinGW64 support
- ✅ Link-Time Optimization (LTO)
- ✅ Anti-bloat plugin
- ✅ Icon support
- ✅ Console/GUI mode selection
- ✅ Parallel compilation

---

### 3. `build_pyinstaller_advanced.py` - Advanced PyInstaller Builder

**Full-featured PyInstaller build script with UPX compression.**

```bash
# Basic builds
python scripts/build_pyinstaller_advanced.py               # Onedir
python scripts/build_pyinstaller_advanced.py --onefile     # Single file

# With compression
python scripts/build_pyinstaller_advanced.py --upx         # Enable UPX
python scripts/build_pyinstaller_advanced.py --onefile --upx

# With icon and GUI mode
python scripts/build_pyinstaller_advanced.py --icon app.ico --no-console

# With data files
python scripts/build_pyinstaller_advanced.py --add-data "data;data"

# Clean build
python scripts/build_pyinstaller_advanced.py --clean --onefile
```

**Features:**
- ✅ UPX compression
- ✅ Icon support
- ✅ Data file inclusion
- ✅ Clean builds
- ✅ Hidden imports handling
- ✅ Console/GUI mode

---

## Build Modes Comparison

| Feature | Nuitka Standalone | Nuitka Onefile | PyInstaller Onedir | PyInstaller Onefile |
|---------|-------------------|----------------|-------------------|---------------------|
| **Output** | Folder with .exe | Single .exe | Folder with .exe | Single .exe |
| **Startup Time** | Fast | Slower | Fast | Slower |
| **Size** | Larger | Medium | Large | Medium |
| **Compilation Time** | Longest | Long | Fast | Fast |
| **Performance** | Best | Best | Good | Good |
| **Antivirus False Positives** | Rare | Rare | Common | More Common |
| **Recommended For** | Production | Distribution | Development | Quick distribution |

---

## Compiler Comparison (Nuitka)

### GCC (MinGW64)
```bash
python scripts/build_nuitka_advanced.py --compiler mingw64
```

**Pros:**
- ✅ Best optimization
- ✅ Smaller binaries
- ✅ Free and open-source
- ✅ Good compatibility

**Cons:**
- ⚠️ Slower compilation
- ⚠️ Need to install MinGW64

**Installation:**
```bash
# Download from https://www.msys2.org/
# Install MinGW64 packages
pacman -S mingw-w64-x86_64-gcc
```

### MSVC (Visual Studio)
```bash
python scripts/build_nuitka_advanced.py --compiler msvc
```

**Pros:**
- ✅ Fast compilation
- ✅ Official Microsoft compiler
- ✅ Best Windows compatibility
- ✅ Good debugging support

**Cons:**
- ⚠️ Larger binaries
- ⚠️ Requires Visual Studio Build Tools

**Installation:**
```bash
# Download Visual Studio Build Tools
# https://visualstudio.microsoft.com/downloads/
```

### Clang
```bash
python scripts/build_nuitka_advanced.py --compiler clang
```

**Pros:**
- ✅ Good optimization
- ✅ Fast compilation
- ✅ Good error messages

**Cons:**
- ⚠️ Need to install LLVM

---

## Quick Start Examples

### Example 1: Simple Web Application

```bash
# Project structure:
my_app/
├── main.py          # Entry point
├── controllers/
│   └── api.py
└── services/
    └── data.py

# Build command:
python scripts/build_app.py --entry my_app/main.py --tool nuitka
```

### Example 2: Production Build (Nuitka + GCC + Optimization)

```bash
python scripts/build_nuitka_advanced.py \
    --entry my_app/main.py \
    --onefile \
    --compiler mingw64 \
    --optimize \
    --icon my_app/icon.ico \
    --no-console
```

### Example 3: Quick Test Build (PyInstaller)

```bash
python scripts/build_pyinstaller_advanced.py \
    --entry my_app/main.py \
    --onefile \
    --clean
```

### Example 4: Distribution Package (PyInstaller + UPX)

```bash
python scripts/build_pyinstaller_advanced.py \
    --entry my_app/main.py \
    --onefile \
    --upx \
    --icon my_app/icon.ico \
    --name MyApplication
```

---

## Configuration in Your Application

**Always configure Cullinan before creating the Application:**

```python
# my_app/main.py

from cullinan import configure, Application

# Configure Cullinan (IMPORTANT for packaging!)
configure(
    user_packages=['my_app'],  # Your application package
    auto_scan=False             # Disable auto-scan for better performance
)

def main():
    app = Application()
    app.run(port=8080)

if __name__ == '__main__':
    main()
```

---

## Troubleshooting

### Issue: "Module not found" after build

**Solution:** Add explicit package configuration:

```python
configure(
    user_packages=['my_app', 'my_app.controllers', 'my_app.services']
)
```

Or use the `--package` flag:
```bash
python scripts/build_app.py --package my_app.controllers --package my_app.services
```

### Issue: Large executable size

**Solutions:**

1. **Use Nuitka with optimization:**
```bash
python scripts/build_nuitka_advanced.py --optimize
```

2. **Use PyInstaller with UPX:**
```bash
python scripts/build_pyinstaller_advanced.py --upx
```

3. **Exclude unnecessary packages:**
```bash
python scripts/build_pyinstaller_advanced.py --exclude-module matplotlib
```

### Issue: Slow startup (onefile mode)

**Solution:** Use standalone/onedir mode instead:
```bash
python scripts/build_app.py --mode standalone
```

### Issue: Antivirus false positive

**Solutions:**

1. **Use Nuitka instead of PyInstaller** (fewer false positives)
2. **Use standalone mode instead of onefile**
3. **Sign your executable with a code signing certificate**
4. **Add exception in antivirus software**

---

## Advanced Topics

### Custom Nuitka Flags

```bash
python scripts/build_nuitka_advanced.py \
    --extra \
    --windows-company-name="My Company" \
    --windows-product-name="My App" \
    --windows-file-version="1.0.0.0" \
    --windows-product-version="1.0.0.0"
```

### Custom PyInstaller Flags

```bash
python scripts/build_pyinstaller_advanced.py \
    --extra \
    --version-file=version.txt \
    --manifest=app.manifest
```

### Including Data Files

```bash
# PyInstaller
python scripts/build_pyinstaller_advanced.py \
    --add-data "templates;templates" \
    --add-data "static;static" \
    --add-data "config.json;."

# Nuitka
python scripts/build_nuitka_advanced.py \
    --extra \
    --include-data-dir=templates=templates \
    --include-data-file=config.json=config.json
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Application

on: [push]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install nuitka
      
      - name: Build with Nuitka
        run: python scripts/build_nuitka_advanced.py --onefile --optimize
      
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: application
          path: dist/
```

---

## Best Practices

1. **✅ Always use `configure()`** in your application
2. **✅ Test in both development and packaged modes**
3. **✅ Use standalone mode for production**
4. **✅ Use onefile mode for simple distribution**
5. **✅ Include version info and icon**
6. **✅ Test on clean machines**
7. **✅ Use code signing for production releases**
8. **⚠️ Avoid hardcoded paths** (use relative paths)
9. **⚠️ Handle resources properly** (use proper resource loading)
10. **⚠️ Test antivirus compatibility**

---

## See Also

- [Configuration Guide](01-configuration.md)
- [Packaging Guide](02-packaging.md)
- [Troubleshooting](03-troubleshooting.md)

