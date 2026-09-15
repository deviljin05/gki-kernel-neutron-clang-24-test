#!/usr/bin/env python3

import glob
import os
import re

# ===== Only 5.10 =====
KERNEL_VERSION = "5.10"


def read_or_default(path, default="*No changelog available*"):
    if os.path.isfile(path):
        return open(path).read().rstrip("\n")
    return default


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def parse_env_file(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                if key:
                    env[key] = value
    return env


def load_build_envs():
    env_files = sorted(glob.glob("release-artifacts/build-env-*.txt"))
    if not env_files:
        raise SystemExit("ERROR: no build-env-*.txt files found in release-artifacts/")

    all_builds = [parse_env_file(f) for f in env_files]

    shared_env = {}
    for key in ("RELEASE_REPO", "RELEASE", "RELEASE_NAME", "KERNEL_NAME"):
        values = {b[key] for b in all_builds if b.get(key)}
        if not values:
            raise SystemExit(f"ERROR: missing required build-env value: {key}")
        shared_env[key] = sorted(values)[0]

    return all_builds, shared_env


def variant_zip_name(build):
    """Reconstruct the exact zip filename build.sh produced for this job."""
    base_name = build.get("BASE_NAME")
    release = build.get("RELEASE")
    linux_version = build.get("LINUX_VERSION")
    if not (base_name and release and linux_version):
        return None
    return f"{base_name}-{release}-{linux_version}.zip"


def variant_link(display_name, filename, repo, tag):
    return f"- [{display_name}](https://github.com/{repo}/releases/download/{tag}/{filename})"


def display_variant_name(build):
    name = build.get("BUILD_VARIANT", "")
    kver = build.get("KERNEL_VERSION", "")
    prefix = f"{kver}-"
    return name[len(prefix):] if name.startswith(prefix) else name


def build_kernel_section(kernel_version, builds, repo, tag, existing_zips, inputs):
    android_release = builds[0].get("ANDROID_RELEASE", "unknown")
    label = f"Android{android_release}-{kernel_version}-LTS"
    anchor_title = f"{label} Files"

    representative = next((b for b in builds if b.get("KSU_SUSFS") == "true"), builds[0])

    file_lines = []
    for b in sorted(builds, key=lambda b: display_variant_name(b)):
        zip_name = variant_zip_name(b)
        if zip_name and zip_name in existing_zips:
            file_lines.append(variant_link(display_variant_name(b), zip_name, repo, tag))
    files_block = "\n".join(file_lines) if file_lines else "- *No build artifacts found*"

    # ===== NH REMOVED =====
    # wireless_block = ...
    # (Removed)

    susfs_changelog_file = f"release-artifacts/susfs_changelog-{kernel_version}.txt"
    susfs_version = representative.get("SUSFS_VERSION", "Not included")

    anchor_id = slugify(label)
    section = f"""<a name="{anchor_id}"></a>
## {anchor_title}

**Downloads:**
{files_block}

**Build details:**
- Linux version: {representative.get('LINUX_VERSION', 'unknown')}
- Compiler: {representative.get('COMPILER_STRING', 'unknown')}
- SuSFS: {susfs_version}

**SuSFS changelog for this line (last 5 commits):**

{read_or_default(susfs_changelog_file)}
"""
    return label, section


def build_release_body():
    all_builds, shared_env = load_build_envs()
    repo = shared_env["RELEASE_REPO"]
    tag = shared_env["RELEASE"]
    release_name = shared_env["RELEASE_NAME"]

    existing_zips = {os.path.basename(p) for p in glob.glob("release-artifacts/*.zip")}

    inputs = {
        # "nh": os.environ.get("NH_INPUT", ""),        # REMOVED
        # "nm": os.environ.get("NM_INPUT", ""),        # REMOVED
        "droidspaces": os.environ.get("DROIDSPACES_INPUT", ""),
        "lto": os.environ.get("LTO_INPUT", ""),
        "test": os.environ.get("TEST_INPUT", ""),
    }
    status_map = {"true": "Enabled", "false": "Disabled"}
    cap_first = lambda s: s[0].upper() + s[1:] if s else s

    warning = (
        "> [!Warning]\n> This is a test release for pipeline debugging - please do not download or install.\n\n"
        if inputs["test"] == "yes"
        else ""
    )

    # ===== Single kernel =====
    label, section = build_kernel_section(KERNEL_VERSION, all_builds, repo, tag, existing_zips, inputs)
    toc_block = f"- [{label}](#{slugify(label)})"
    sections_block = section

    body = f"""{warning}### {release_name}

## ❤️ Support This Project

**[Donations](https://github.com/ahmed-alnassif#-support-my-work)**

Your donations keep this project alive! I spend countless hours maintaining kernel builds for 5 different versions, fixing bugs, adding features, and supporting users. **Every donation matters!** 🙏

- **[ReSuSFS](https://github.com/ahmed-alnassif/ReSuSFS)** – Root hiding made simple, powerful when you need it.

- **Community:** join the discussion and get support on [Telegram](https://t.me/ahmed_alnassif_tg).

**Run settings:**
- LTO optimizations: {cap_first(inputs['lto']) or 'Unknown'}
- DroidSpaces: {status_map.get(inputs['droidspaces'], 'Disabled')}

> [!Important]
> These are **GKI** kernels, not custom kernels. This line supports **all** devices that shipped with Linux {KERNEL_VERSION} and Android 12 (stock or AOSP).

## 🧭 Which variant should I flash?

| Variant | Root | SuSFS | LTO | Compat |
|---------|------|-------|-----|--------|
| KernelSU+SuSFS | ✅ | ✅ | Full | ❌ |
| KSU+SuSFS+MM | ✅ | ✅ | Full | ❌ |
| ReSukiSU+SuSFS | ✅ | ✅ | Full | ❌ |
| Compat+KSU+SuSFS | ✅ | ✅ | ❌ | ✅ |
| Compat+ReSukiSU+SuSFS | ✅ | ✅ | ❌ | ✅ |

**Not sure? Use a `Compat` variant first**: it fixes most boot issues.

## Contents
{toc_block}

---

{sections_block}

---

>[!Note]
>- **Bootloop?** Flash a **Compat** variant first.
>- **Issues?** Check [Discussions](https://github.com/ahmed-alnassif/GKID-Kernels/discussions) before opening an issue.

---

### Community & Support
- **Have questions?** Start a [Discussion](https://github.com/ahmed-alnassif/GKID-Kernels/discussions)
- **Found a bug?** Open an [Issue](https://github.com/ahmed-alnassif/GKID-Kernels/issues) with logs
- **Enjoying the kernel?** Star the [repo](https://github.com/ahmed-alnassif/GKID-Kernels)

---

**Performance & battery optimizations**
Engineered for smoother UI, better multitasking, and gaming:

**Performance**
- 300Hz timer -> lower input lag, snappier feel
- MGLRU -> better multitasking & battery life
- Faster memory ops -> up to 50% faster string/memory handling
- mq-deadline I/O -> low-latency on UFS storage
- CPU governors: schedutil + ondemand -> efficient & responsive
- NTSync driver -> faster Windows games/apps on Winlator/GameHub

**Network**
- TCP BBRv3 + Westwood+ -> better WiFi/mobile data speeds
- IPv6 NAT + IP Set -> better tethering & VPN

**Battery life**
- Wakelock cap: 500ms -> prevents battery drain
- Freeze timeout: 20s -> 1s -> faster deadlock detection
- ext4 commit age: 30s -> fewer disk writes
- Minimized alarm wakeups -> less standby drain

**Storage & filesystem**
- F2FS tuning: reduced GC sleep (50ms) -> smoother I/O
- ext4 optimization -> extended commit age

**Security**
- Baseband Guard (BBG) -> blocks unauthorized writes to critical partitions

---

>[!Tip]
>This kernel includes **TCP BBRv3** (default) and **Westwood+** congestion control algorithms.
>You can switch between them - changes are temporary and reset after reboot.

**Switch to Westwood+ (better for some networks):**
```bash
su -c "sysctl -w net.ipv4.tcp_congestion_control=westwood"
