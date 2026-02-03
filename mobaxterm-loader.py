#!/usr/bin/env python3
import argparse
import sys
import requests
import re
import zipfile
import os
from urllib.parse import urljoin

# ==========================================================
# Variant Base64 tables (custom, NOT RFC-4648)
# ==========================================================
VARIANT_BASE64_TABLE = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
VARIANT_BASE64_DICT = {i: v for i, v in enumerate(VARIANT_BASE64_TABLE)}

# ==========================================================
# License type enum + names
# ==========================================================
class LicenseType:
    Professional = 1
    Educational  = 3
    Personal     = 4

    @classmethod
    def from_string(cls, value):
        mapping = {
            "professional": cls.Professional,
            "educational":  cls.Educational,
            "personal":     cls.Personal,
        }
        try:
            return mapping[value.lower()]
        except KeyError:
            raise ValueError("Invalid LicenseType. Choose: Professional, Educational, Personal")


LICENSE_TYPE_NAMES = {
    LicenseType.Professional: "Professional",
    LicenseType.Educational:  "Educational",
    LicenseType.Personal:     "Personal",
}

# ==========================================================
# Helpers
# ==========================================================
def bytes_to_int_le(bs, offset=0):
    b0 = bs[offset] if offset < len(bs) else 0
    b1 = bs[offset + 1] if offset + 1 < len(bs) else 0
    b2 = bs[offset + 2] if offset + 2 < len(bs) else 0
    b3 = bs[offset + 3] if offset + 3 < len(bs) else 0
    return (b0 & 0xFF) | ((b1 & 0xFF) << 8) | ((b2 & 0xFF) << 16) | ((b3 & 0xFF) << 24)


def str_to_bytes(s):
    return list(s.encode("utf-8"))


def bytes_to_str(bs):
    return bytes(bs).decode("utf-8", errors="ignore")


def variant_base64_encode(bs):
    result = []
    blocks_count = len(bs) // 3
    left_bytes = len(bs) % 3

    for i in range(blocks_count):
        coding_int = bytes_to_int_le(bs[3 * i : 3 * i + 3] + [0])
        block = (
            VARIANT_BASE64_DICT[coding_int & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 12) & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 18) & 0x3F]
        )
        result.append(block)

    if left_bytes == 1:
        coding_int = bytes_to_int_le(bs[-1:] + [0, 0])
        block = (
            VARIANT_BASE64_DICT[coding_int & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3F]
        )
        result.append(block)

    elif left_bytes == 2:
        coding_int = bytes_to_int_le(bs[-2:] + [0])
        block = (
            VARIANT_BASE64_DICT[coding_int & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3F] +
            VARIANT_BASE64_DICT[(coding_int >> 12) & 0x3F]
        )
        result.append(block)

    return ''.join(result)


def encrypt_bytes(key, bs):
    result = []
    for val in bs:
        enc = val ^ ((key >> 8) & 0xFF)
        result.append(enc)
        key = (enc & key) | 0x482D
    return result


def generate_license(lic_type, user_name, count, major, minor):
    license_source = (
        f"{lic_type}#{user_name}|"
        f"{major}{minor}#"
        f"{count}#"
        f"{major}3{minor}6{minor}"
        f"#0#0#0#"
    )
    encrypted = encrypt_bytes(0x787, str_to_bytes(license_source))
    encoded = variant_base64_encode(encrypted)
    return encoded


# ==========================================================
# Main
# ==========================================================
def main():
    parser = argparse.ArgumentParser(
        description="Download MobaXterm (Portable/Installer, stable or preview) + generate & embed license"
    )
    parser.add_argument("license_type", nargs='?', default="Educational",
                        help="Professional | Educational | Personal (default: Educational)")
    parser.add_argument("user_name",   nargs='?', default="Majin Buu",
                        help="User name / license owner (default: Majin Buu)")
    parser.add_argument("version",     nargs='?', default="25.4",
                        help="Version <major>.<minor> (default: 25.4 – used for license only)")
    parser.add_argument("count",       nargs='?', type=int, default=2,
                        help="Number of supported users (default: 2)")
    parser.add_argument("--output-base-dir", default=".",
                        help="Directory for download and extraction (default: current)")
    parser.add_argument("--keep-pro-key", action="store_true",
                        help="Keep temporary Pro.key file after creating Custom.mxtpro")
    parser.add_argument("--installer", action="store_true",
                        help="Download the Installer edition instead of Portable")
    parser.add_argument("--preview", action="store_true",
                        help="Download from preview channel (latest preview build) instead of stable")

    args = parser.parse_args()

    if args.count > 9999:
        print("⚠️  Warning: count > 9999 – MobaXterm may ignore or clip the value", file=sys.stderr)

    # Validate version (used for license generation, not download detection)
    if "." not in args.version:
        print("❌ Version must be <major>.<minor>", file=sys.stderr)
        sys.exit(1)
    major_str, minor_str = args.version.split(".", 1)
    if not major_str.isdigit() or not minor_str.isdigit():
        print("❌ Major and minor must be numeric", file=sys.stderr)
        sys.exit(1)
    major = int(major_str)
    minor = int(minor_str)

    # Get license type
    try:
        lic_type = LicenseType.from_string(args.license_type)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if args.preview:
        URL = "https://mobaxterm.mobatek.net/preview.html"
        channel = "Preview"
    else:
        URL = "https://mobaxterm.mobatek.net/download-home-edition.html"
        channel = "Stable"

    edition = "Installer" if args.installer else "Portable"
    print(f"🌐 Fetching MobaXterm {channel} page... (looking for {edition} edition)")

    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {channel} page: {e}", file=sys.stderr)
        sys.exit(1)

    print("🔎 Looking for latest ZIP...")
    # Regex matches both Portable/Installer and handles _PreviewN
    matches = re.findall(r'href="([^"]*MobaXterm_(Portable|Installer)_v[\d.]+(?:_Preview\d+)?\.zip)"',
                         response.text, re.IGNORECASE)

    if not matches:
        print(f"❌ No MobaXterm ZIP links found on {channel} page.", file=sys.stderr)
        print(f"   → Check manually: {URL}")
        sys.exit(1)

    # Pick the correct edition
    selected_url = None
    selected_filename = None
    target_edition = "Installer" if args.installer else "Portable"

    for href, ed in matches:
        if ed.lower() == target_edition.lower():
            selected_url = urljoin(URL, href)
            selected_filename = os.path.basename(href)
            break

    if not selected_url:
        print(f"❌ Could not find {target_edition} ZIP on {channel} page.", file=sys.stderr)
        sys.exit(1)

    print(f"📦 Found {channel} {target_edition}: {selected_filename}")
    print(f"    URL:  {selected_url}")

    base_dir    = args.output_base_dir
    zip_path    = os.path.join(base_dir, selected_filename)
    extract_dir = os.path.join(base_dir, os.path.splitext(selected_filename)[0])

    # Download (skip if exists)
    if not os.path.isfile(zip_path):
        print("⬇️ Downloading...")
        try:
            with requests.get(selected_url, headers=HEADERS, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            print(f"❌ Download failed: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"✅ Downloaded: {zip_path}")
    else:
        print(f"✓ ZIP already exists: {zip_path} → skipping download")

    # Check if already extracted + licensed
    moba_exe_found = False
    exe_name = None
    license_already_present = os.path.isfile(os.path.join(extract_dir, "Custom.mxtpro"))

    if os.path.isdir(extract_dir):
        for file in os.listdir(extract_dir):
            if file.lower().startswith("mobaxterm") and file.lower().endswith(".exe"):
                moba_exe_found = True
                exe_name = file
                break

    if moba_exe_found:
        if license_already_present:
            print(f"✓ Folder already looks complete: contains {exe_name} + Custom.mxtpro")
            print(f"   → Regenerating license anyway (Ctrl+C to cancel if not needed)")
        else:
            print(f"✓ Found {exe_name} but no Custom.mxtpro yet → generating license")
    else:
        print(f"📂 Extracting to: {extract_dir}")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            print("🎉 Extraction completed!")
        except Exception as e:
            print(f"❌ Extraction failed: {e}", file=sys.stderr)
            sys.exit(1)

    # Generate & embed license
    license_key = generate_license(lic_type, args.user_name, args.count, major, minor)
    print(f"\n🔑 Generated {LICENSE_TYPE_NAMES[lic_type]} license:")
    print("")
    print("   Key      :", license_key)
    print("   User     :", args.user_name)
    print("   Version  :", args.version)
    print("   Users    :", args.count)
    print("")

    key_path    = os.path.join(extract_dir, "Pro.key")
    mxtpro_path = os.path.join(extract_dir, "Custom.mxtpro")

    try:
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(license_key + "\n")

        with zipfile.ZipFile(mxtpro_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(key_path, arcname="Pro.key")

        print(f"✓ Created / Updated: {mxtpro_path}")
        print(f"   → Placed in extracted root: {extract_dir}")

        if not args.keep_pro_key:
            try:
                os.remove(key_path)
                print("   (temporary Pro.key removed)")
            except:
                pass

        print("\nReady to use:")
        print(f"   → Launch: {os.path.join(extract_dir, exe_name or 'MobaXterm.exe')}")
        print("   → License should be active automatically 🎉")

    except Exception as e:
        print(f"❌ Failed to create license files: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()