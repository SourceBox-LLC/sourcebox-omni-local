import psutil
import platform


def system_info(info_type: str = "all") -> str:
    """
    Return system info as JSON text.
    info_type: 'all', 'cpu', 'memory', 'disk', 'network', 'os', 'processes'
    """
    data = {}
    if info_type in ("all", "cpu"):
        data["cpu_percent"] = psutil.cpu_percent(interval=1)
    if info_type in ("all", "memory"):
        data["memory"] = psutil.virtual_memory()._asdict()
    if info_type in ("all", "disk"):
        data["disk"] = {
            d.mountpoint: psutil.disk_usage(d.mountpoint)._asdict()
            for d in psutil.disk_partitions()
        }
    if info_type in ("all", "network"):
        data["network"] = psutil.net_io_counters()._asdict()
    if info_type in ("all", "os"):
        data["os"] = {
            "system": platform.system(),
            "release": platform.release()
        }
    if info_type in ("all", "processes"):
        data["processes"] = [
            p.info for p in psutil.process_iter(["pid", "name", "username"])
        ]

    import json
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    info_type = "all"
    result = system_info(info_type)
    print(result)
