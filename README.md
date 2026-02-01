# 🚀 MobaXterm Portable + Custom License Generator

#### **One-click script** to:
```
- 📥 Download the **latest MobaXterm Portable** edition
- 🗄️ Extract it automatically
- 🔑 Generate a valid-looking Professional / Educational / Personal license key
- 🗜️ Create `Custom.mxtpro` and place it directly inside the extracted folder
```
So you can launch a fully "activated" portable MobaXterm without manual copying! 🎉

> ⚠️ **Disclaimer**
> This is for **educational & research purposes only**.
> Using generated license keys in production / commercial environments violates MobaXterm's license agreement.
> Please consider purchasing an official license from [mobatek.net](https://mobaxterm.mobatek.net) if you use it professionally 💼

## ✨ Features
```
- Automatically finds & downloads latest portable ZIP from official site
- Extracts to a nicely named folder (e.g. `MobaXterm_Portable_v25.4`)
- Generates license compatible with current versions (tested up to early 2026)
- Creates `Custom.mxtpro` **directly in the portable root** → ready to run!
- Nice progress bars with `tqdm` 📊
- Clean CLI with helpful error messages
```
## 📋 Requirements

- Python 3.8+
- Internet connection
- Required packages:
```bash
pip install requests tqdm
```

## 🚀 Quick Start
```Bash
# 1. Save the script as e.g. mobaxterm-loader.py
# 2. Run it like this:

./mobaxterm-loader.py Professional "Goku" 25.4 9000

# Or for educational license with many users:
./mobaxterm-loader.py Educational "Vegeta" 25.4 5000

# Want files in a specific folder?
./mobaxterm-loader.py Personal "Majin Buu" 26.0 1 --output-base-dir ./my-portable-moba
```


**After running** → look inside the extracted folder (e.g. ./MobaXterm_Portable_v25.4/):
```yaml
MobaXterm.exe ← double-click to launch
Custom.mxtpro ← already there → license should be active 🎈
```

## 🛠️ Full Usage
```yaml
usage: mobaxterm-loader.py [-h] [--output-base-dir OUTPUT_BASE_DIR]
                            license_type user_name version count

Download latest MobaXterm Portable, generate license, place Custom.mxtpro

positional arguments:
  license_type          License type:  Educational | Personal | Professional
  user_name             User name / license owner
  version               Version in format <major>.<minor> (e.g. 26.0)
  count                 Number of supported users

options:
  -h, --help            show this help message and exit
  --output-base-dir OUTPUT_BASE_DIR
                        Base directory for download & extraction (default: current)
```

## ⚡ Example Outputs
```text
🌐 Fetching MobaXterm download page...
🔎 Looking for latest Portable ZIP...
📦 Found: MobaXterm_Portable_v25.4.zip
⬇️ Downloading...
Download: 100%|█████████████████████| 38.2M/38.2M [00:12<00:00, 3.1MB/s]
✅ Downloaded: MobaXterm_Portable_v25.4.zip
📂 Extracting to: MobaXterm_Portable_v25.4 ...
🎉 Extraction done!

🔑 Generated license key:
MCoCAoIBAA...very-long-base64-string...==

✓ Created ./MobaXterm_Portable_v25.4/Custom.mxtpro
   → Custom.mxtpro is now in the portable root folder
Ready to use: Launch MobaXterm.exe from ./MobaXterm_Portable_v25.4/
```

## ❤️ Credits & Thanks
```yaml
Original license generation logic → community reverse-engineering efforts
Download & progress magic → requests + tqdm
Made with love (and many ☕) in 2026
```
### Enjoy responsibly! 🐧✨
