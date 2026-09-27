"""C盘深度扫描 - 找出大文件夹和文件"""
import io
import os, shutil, json, sys
from collections import defaultdict

C = "C:\\"
SKIP_DIRS = {
    "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "System Volume Information", "$Recycle.Bin", "Recovery",
    "PerfLogs", "Config.Msi", "MSOCache", "Intel", "AMD",
    "drivers", "boot", "efi", "System32", "SysWOW64",
    "WinSxS", "assembly", "Installer", "winsxs",
    "Microsoft.NET", "Microsoft shared", "MSBuild",
    "ModifiableWindowsApps", "WindowsApps",
    "Packages", "ServiceProfiles", "servicing",
    "Resources", "security", "Registration",
    "Help", "Fonts", "INF", "IME", "InputMethod",
    "L2Schemas", "Logs", "Media", "MiracastView",
    "PLA", "PolicyDefinitions", "Prefetch",
    "RemotePackages", "SchCache", "Schemas",
    "security", "ShellExperiences", "ShellComponents",
    "SKB", "Speech", "Speech_OneCore",
    "System", "system32", "SysWOW64",
    "TAPI", "Tasks", "Temp", "tracing",
    "Vss", "Web", "WindowsPowerShell",
    "WMSysPr9", "wudrv", "WaaSMedicAgent",
    "WLXPG", "WTC", "CSC", "Cursors",
    "Debug", "DiagTrack", "DigitalLocker",
    "Downloaded Program Files", "en-US",
    "FileManager", "GameBarPresenceWriter",
    "GamingRoot", "Globalization", "Branding",
    "appcompat", "AppReadiness", "AppResolver",
    "AppPatch", "bcastdvr", "BitLockerDiscoveryVolumeContents",
    "Bluetooth", "bthprops", "capicom",
    "Common Files", "Comms", "Containers",
    "Crypto", "DataShare", "DIFx",
    "DiagTrack", "diagnostics", "DirectX",
    "DispDref", "dot3svc", "Downloaded Installations",
    "DriverStore", "DTSS", "DVR",
    "EmbeddedLockdownFiles", "Empty", "en",
    "Enrollment", "EventSystem", "FileManager",
    "FileWrites", "Fusion", "GameExplorer",
    "GetHelp", "Globalization", "Help",
    "HoloShell", "HotSwap", "IIS",
    "ImmersiveControlPanel", "Indexer", "InputMethod",
    "IoT", "LanguageOverlay", "LAP",
    "LiveKernelReports", "LocationProvider",
    "Mail", "Maps", "MediaViewer",
    "Merchant", "MI", "Migration",
    "Minidump", "MixedReality", "mmres",
    "ModemLogs", "MUI", "ndpp",
    "Network", "NetworkLocationWizard",
    "NLB", "Notepad", "OEM",
    "Oobe", "OpenSSH", "OptionalFeatures",
    "PCL", "PE", "Phone",
    "PhotoViewer", "PointOfService", "PolicyManager",
    "PowerShell", "PrintDialog", "Printing_Admin_Scripts",
    "Privacy", "Provisioning", "ProvisioningHandlers",
    "PW", "Ras", "Refs",
    "RemoteAssistance", "RemoteDesktop", "Resources",
    "Rights", "RMA", "RSoP",
    "ScreenOnTime", "Search", "SecureBootUpdates",
    "SecurityAndMaintenance", "Sensor", "Servicing",
    "Setup", "Shared", "ShellComponents",
    "ShellExperiences", "SKB", "SleepStudy",
    "SoftwareDistribution", "Speech", "Speech_OneCore",
    "Spool", "Startup", "Storage",
    "Store", "Streams", "Support",
    "Surface", "Symbols", "System",
    "SystemApps", "SystemResources", "Tablet",
    "Tasks", "Temp", "TemporaryItems",
    "TextInput", "Themes", "Time",
    "ToastData", "TokenBroker", "Tpm",
    "tskill", "TWIN", "UCI",
    "UI", "UIA", "UIRibbon",
    "Update", "UPnP", "VAN",
    "Vault", "WaaS", "Wallet",
    "WBEM", "WCN", "WDI",
    "WER", "WindowsMail", "WindowsUpdate",
    "WinHttp", "WinML", "WinRM",
    "WISP", "WLAN", "WMI",
    "Work", "WPB", "WRC",
    "WSUS", "WU", "Wwan",
    "Xbox", "XPS", "zh-CN",
    "zh-HK", "zh-TW", "ja-JP", "ko-KR",
    "node_modules",  # 我们单独扫描
}

# 用户目录下的跳过项
SKIP_USER = {
    "AppData\\Local\\Microsoft\\Windows\\INetCache",
    "AppData\\Local\\Temp",
    "AppData\\Local\\Microsoft\\Windows\\Caches",
    "AppData\\Local\\Microsoft\\Windows\\WER",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent",
    "AppData\\Local\\Microsoft\\Terminal Server Client",
    "AppData\\Local\\Microsoft\\Windows\\WebCache",
    "AppData\\Local\\Packages",  # UWP apps
    "AppData\\Local\\Microsoft\\Windows\\Notifications",
    "AppData\\Local\\Microsoft\\Windows\\AppCache",
    "AppData\\Roaming\\Microsoft\\Windows\\Themes",
    "AppData\\Local\\D3DSCache",
    "AppData\\Local\\Microsoft\\OneDrive\\logs",
    "AppData\\Local\\ConnectedDevicesPlatform",
    "AppData\\Local\\Comms",
    "AppData\\Local\\FontCache",
    "AppData\\Local\\Microsoft\\VSCommon",
    "AppData\\Local\\Microsoft\\Vault",
    "AppData\\Local\\Microsoft\\Windows\\ActionCenterCache",
    "AppData\\Local\\Microsoft\\Windows\\AppRepository",
    "AppData\\Local\\Microsoft\\Windows\\Burn",
    "AppData\\Local\\Microsoft\\Windows\\CloudStore",
    "AppData\\Local\\Microsoft\\Windows\\Cortana",
    "AppData\\Local\\Microsoft\\Windows\\DateTime",
    "AppData\\Local\\Microsoft\\Windows\\Explorer",
    "AppData\\Local\\Microsoft\\Windows\\FileHistory",
    "AppData\\Local\\Microsoft\\Windows\\GameExplorer",
    "AppData\\Local\\Microsoft\\Windows\\IECompatCache",
    "AppData\\Local\\Microsoft\\Windows\\IECompatData",
    "AppData\\Local\\Microsoft\\Windows\\LanguageAssigned",
    "AppData\\Local\\Microsoft\\Windows\\LocationHistory",
    "AppData\\Local\\Microsoft\\Windows\\Mail",
    "AppData\\Local\\Microsoft\\Windows\\MediaPlayer",
    "AppData\\Local\\Microsoft\\Windows\\MUI",
    "AppData\\Local\\Microsoft\\Windows\\Multimedia",
    "AppData\\Local\\Microsoft\\Windows\\NetCache",
    "AppData\\Local\\Microsoft\\Windows\\NetCrawl",
    "AppData\\Local\\Microsoft\\Windows\\Notifications",
    "AppData\\Local\\Microsoft\\Windows\\Offline Web Pages",
    "AppData\\Local\\Microsoft\\Windows\\PowerShell",
    "AppData\\Local\\Microsoft\\Windows\\RetailDemo",
    "AppData\\Local\\Microsoft\\Windows\\Ringtones",
    "AppData\\Local\\Microsoft\\Windows\\SettingSync",
    "AppData\\Local\\Microsoft\\Windows\\Speech",
    "AppData\\Local\\Microsoft\\Windows\\SyncCenter",
    "AppData\\Local\\Microsoft\\Windows\\SyncShare",
    "AppData\\Local\\Microsoft\\Windows\\Theme",
    "AppData\\Local\\Microsoft\\Windows\\UPnPDeviceHost",
    "AppData\\Local\\Microsoft\\Windows\\WER",
    "AppData\\Local\\Microsoft\\Windows\\WlanPower",
    "AppData\\Local\\Microsoft\\Windows\\WMF",
    "AppData\\Local\\PeerDistRepub",
    "AppData\\Local\\Publishers",
    "AppData\\Local\\Temp",
    "AppData\\Roaming\\Adobe",
    "AppData\\Roaming\\Microsoft\\Windows\\Cookies",
    "AppData\\Roaming\\Microsoft\\Windows\\Network Shortcuts",
    "AppData\\Roaming\\Microsoft\\Windows\\Printer Shortcuts",
    "AppData\\Roaming\\Microsoft\\Windows\\Recent",
    "AppData\\Roaming\\Microsoft\\Windows\\SendTo",
    "AppData\\Roaming\\Microsoft\\Windows\\Start Menu",
    "AppData\\Roaming\\Microsoft\\Windows\\Templates",
}

def get_size(path):
    try:
        return os.path.getsize(path)
    except:
        return 0

def scan_folder(path, max_depth=3, depth=0):
    """扫描文件夹，返回 {path: size_bytes} 映射"""
    result = {}
    if depth > max_depth:
        return result
    try:
        entries = list(os.scandir(path))
    except (PermissionError, FileNotFoundError, OSError):
        return result
    
    for entry in entries:
        try:
            if entry.is_file():
                result[entry.path] = entry.stat().st_size
            elif entry.is_dir():
                name = entry.name
                # 跳过系统目录
                if depth == 0 and name in SKIP_DIRS:
                    continue
                # 跳过用户目录下的特定子目录
                rel = entry.path.replace(C, "").lstrip("\\")
                if any(rel.startswith(s) for s in SKIP_USER):
                    continue
                sub = scan_folder(entry.path, max_depth, depth+1)
                result.update(sub)
        except (PermissionError, FileNotFoundError, OSError):
            continue
    return result

def aggregate_by_parent(paths, top_n=50):
    """按父目录汇总"""
    dirs = defaultdict(int)
    for p, sz in paths.items():
        parent = os.path.dirname(p)
        dirs[parent] += sz
    return sorted(dirs.items(), key=lambda x: -x[1])[:top_n]

def main():
    print("=" * 70)
    print("C盘深度扫描 - 大文件夹排行")
    print("=" * 70)
    
    # 1. 基础信息
    import ctypes
    free_bytes = ctypes.c_ulonglong(0)
    total_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        "C:\\", None, ctypes.byref(total_bytes), ctypes.byref(free_bytes)
    )
    total_gb = total_bytes.value / 1e9
    free_gb = free_bytes.value / 1e9
    used_gb = total_gb - free_gb
    print(f"总容量: {total_gb:.1f} GB")
    print(f"已用:   {used_gb:.1f} GB")
    print(f"剩余:   {free_gb:.1f} GB ({free_gb/total_gb*100:.1f}%)")
    print()
    
    # 2. 顶级目录大小
    print("--- 顶级目录大小 ---")
    top_level = []
    try:
        for e in os.scandir("C:\\"):
            if e.is_dir() and e.name not in SKIP_DIRS:
                try:
                    sz = 0
                    for root, dirs, files in os.walk(e.path, topdown=True):
                        # 跳过 Windows 内部的子目录
                        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                        for f in files:
                            try:
                                fp = os.path.join(root, f)
                                sz += os.path.getsize(fp)
                            except:
                                pass
                    top_level.append((e.name, sz))
                except:
                    pass
    except:
        pass
    
    top_level.sort(key=lambda x: -x[1])
    for name, sz in top_level[:30]:
        if sz > 100 * 1024 * 1024:  # >100MB
            print(f"  {name:40s} {sz/1e9:.2f} GB")
    
    print()
    
    # 3. 用户目录大项
    user = os.environ.get("USERPROFILE", "C:\\Users\\Administrator")
    print(f"--- 用户目录 ({user}) 大项 ---")
    user_items = []
    try:
        for e in os.scandir(user):
            if e.is_dir():
                try:
                    sz = 0
                    for root, dirs, files in os.walk(e.path, topdown=True):
                        # 跳过node_modules
                        dirs[:] = [d for d in dirs if d != "node_modules"]
                        for f in files:
                            try:
                                sz += os.path.getsize(os.path.join(root, f))
                            except:
                                pass
                    user_items.append((e.name, sz))
                except:
                    pass
    except:
        pass
    
    user_items.sort(key=lambda x: -x[1])
    for name, sz in user_items[:20]:
        if sz > 10 * 1024 * 1024:  # >10MB
            print(f"  {name:40s} {sz/1e9:.2f} GB")
    
    print()
    
    # 4. 大文件TOP 30
    print("--- 大文件 TOP 30 ---")
    big_files = []
    for root, dirs, files in os.walk("C:\\", topdown=True):
        # 跳过系统目录
        rel = root.replace("C:\\", "").lstrip("\\")
        skip = False
        for s in SKIP_DIRS:
            if rel.startswith(s) or rel == s:
                skip = True
                break
        if skip:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d != "node_modules"]
        for f in files:
            try:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                if sz > 100 * 1024 * 1024:  # >100MB
                    big_files.append((fp, sz))
            except:
                pass
    
    big_files.sort(key=lambda x: -x[1])
    for fp, sz in big_files[:30]:
        print(f"  {sz/1e9:.2f} GB  {fp}")
    
    print()
    
    # 5. node_modules 汇总
    print("--- node_modules 占用 ---")
    nm_total = 0
    nm_list = []
    for root, dirs, files in os.walk("C:\\", topdown=True):
        if os.path.basename(root) == "node_modules":
            try:
                sz = 0
                for r2, d2, f2 in os.walk(root):
                    for f in f2:
                        try:
                            sz += os.path.getsize(os.path.join(r2, f))
                        except:
                            pass
                nm_list.append((root, sz))
                nm_total += sz
                dirs[:] = []  # 不继续深入
            except:
                pass
        else:
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    
    nm_list.sort(key=lambda x: -x[1])
    for p, sz in nm_list[:10]:
        print(f"  {sz/1e6:.1f} MB  {p}")
    print(f"  node_modules 总计: {nm_total/1e9:.2f} GB")
    
    print()
    
    # 6. 缓存清理建议
    print("--- 缓存清理建议 ---")
    cache_paths = [
        (os.path.expanduser("~\\AppData\\Local\\Temp"), "Temp"),
        (os.path.expanduser("~\\AppData\\Local\\npm-cache"), "npm-cache"),
        (os.path.expanduser("~\\AppData\\Local\\pip\\cache"), "pip cache"),
        (os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\INetCache"), "IE/Edge缓存"),
        (os.path.expanduser("~\\AppData\\Local\\CrashDumps"), "CrashDumps"),
        (os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache"), "Chrome缓存"),
        (os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache"), "Edge缓存"),
        ("C:\\Windows\\Temp", "Windows Temp"),
        ("C:\\Windows\\SoftwareDistribution\\Download", "Windows Update缓存"),
        (os.path.expanduser("~\\AppData\\Local\\Temp\\pip"), "pip temp"),
    ]
    for path, label in cache_paths:
        if os.path.exists(path):
            try:
                sz = 0
                for root, dirs, files in os.walk(path):
                    for f in files:
                        try:
                            sz += os.path.getsize(os.path.join(root, f))
                        except:
                            pass
                if sz > 10 * 1024 * 1024:
                    print(f"  {sz/1e6:.1f} MB  {label} ({path})")
            except:
                pass

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()