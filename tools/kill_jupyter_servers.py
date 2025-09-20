import subprocess
import os
import time

def kill_processes(process_substring):
    """Find and kill processes matching a substring in their command line."""
    try:
        # Find process IDs using pgrep with the specified substring
        # -f: match against the full argument list
        pgrep_output = subprocess.check_output(["pgrep", "-f", process_substring]).decode().strip()

        if pgrep_output:
            pids = pgrep_output.splitlines()
            print(f"Found processes matching '{process_substring}' with PIDs: {pids}")
            for pid in pids:
                try:
                    # Kill the process
                    os.kill(int(pid), 9)
                    print(f"Killed process {pid}")
                    time.sleep(1) # Give the process a moment to terminate
                except ProcessLookupError:
                    print(f"Process {pid} already terminated.")
                except Exception as e:
                    print(f"An error occurred while killing process {pid}: {e}")
        else:
            print(f"No process found matching '{process_substring}'.")

    except subprocess.CalledProcessError:
        print(f"No process found matching '{process_substring}'.")
    except Exception as e:
        print(f"An error occurred while searching for '{process_substring}': {e}")

# Kill the custom jupyter lab process
kill_processes("jupyter lab --ServerApp.ip=0.0.0.0")

# Kill the cloudflared tunnel process
kill_processes("cloudflared tunnel --url")