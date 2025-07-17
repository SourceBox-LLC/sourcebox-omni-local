# Import subprocess for running shell commands
import subprocess

def shell(command: str) -> str:
    """Run a Windows shell command; return stdout or stderr."""
    try:
        # Add timeout to prevent hanging commands
        out = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True, timeout=20
        )
        return out
    except subprocess.CalledProcessError as e:
        return f"Error (code {e.returncode}): {e.output}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


if __name__ == "__main__":
    command = "ipconfig"
    result = shell(command)
    print(result)