import platform
import subprocess

def kill_desktop_browser(log=None) -> bool:
    """
    Kill Chrome/Chromium on macOS / Windows / Linux.
    """
    os_name = platform.system()
    if log: log.warning(f"OS Browser Kill initiated for: {os_name}", tags=["OS", "KILL"])

    if os_name == "Darwin":
        cmd = ["killall", "Google Chrome"]
    elif os_name == "Windows":
        cmd = ["taskkill", "/F", "/IM", "chrome.exe"]
    elif os_name == "Linux":
        cmd = ["pkill", "-f", "chrome"]
    else:
        return False

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except:
        return False