"""
Manual test for per-process GPU stats in NvidiaMonitorPlugin.

Verifies that the 'processes' list in the GPU details is populated
with per-process GPU memory usage data.

Usage:
    conda activate cjm-system-monitor-nvidia
    python tests_manual/test_gpu_processes.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cjm_system_monitor_nvidia.plugin import NvidiaMonitorPlugin


def test_system_stats():
    """Test that execute() returns system stats with per-process GPU data."""
    print("=== SYSTEM STATS TEST ===\n")

    plugin = NvidiaMonitorPlugin()
    plugin.initialize()

    stats = plugin.execute("get_system_status")

    # System-level stats
    print("--- System ---")
    print(f"  CPU: {stats['cpu_percent']:.1f}%")
    print(f"  RAM: {stats['memory_used_mb']:.0f}MB / {stats['memory_total_mb']:.0f}MB "
          f"({stats['memory_available_mb']:.0f}MB available)")

    # GPU aggregate stats
    print(f"\n--- GPU Aggregate ---")
    print(f"  Type: {stats['gpu_type']}")
    print(f"  VRAM: {stats['gpu_used_memory_mb']:.0f}MB / {stats['gpu_total_memory_mb']:.0f}MB "
          f"({stats['gpu_free_memory_mb']:.0f}MB free)")
    print(f"  Load: {stats['gpu_load_percent']:.0f}%")

    # Per-device details
    details = stats.get('details', {})
    gpu_details = details.get('details', {})
    print(f"\n--- Per-Device ({len(gpu_details)} GPUs) ---")
    for gpu_key, gpu_data in gpu_details.items():
        print(f"  {gpu_key}: {gpu_data.get('name', 'unknown')}")
        print(f"    Memory: {gpu_data.get('memory_used', 0)}MB / {gpu_data.get('memory_total', 0)}MB")
        print(f"    Utilization: {gpu_data.get('utilization', 0)}%")

    # Per-process GPU stats (NEW)
    processes = details.get('processes', [])
    print(f"\n--- GPU Processes ({len(processes)}) ---")
    if processes:
        for proc in processes:
            cmd = proc.get('command', '')
            cmd_display = f" [{cmd[:60]}...]" if len(cmd) > 60 else f" [{cmd}]" if cmd else ""
            print(f"  PID {proc['pid']}: {proc['gpu_memory_mb']}MB on GPU {proc['gpu_index']}{cmd_display}")
    else:
        print("  No GPU processes found.")
        print("  (This is expected if no GPU-using processes are running.)")

    print(f"\n--- Test Result ---")
    print(f"  Processes list populated: {'YES' if processes else 'NO (none running)'}")
    print(f"  Stats structure valid: YES")


def test_raw_gpu_info():
    """Test _get_gpu_info_internal() directly."""
    print("\n=== RAW GPU INFO TEST ===\n")

    plugin = NvidiaMonitorPlugin()
    gpu_info = plugin._get_gpu_info_internal()

    print(f"Available: {gpu_info['available']}")
    print(f"Type: {gpu_info['type']}")
    print(f"Devices: {len(gpu_info['details'])}")
    print(f"Processes: {len(gpu_info['processes'])}")
    print(f"\nFull output:")
    print(json.dumps(gpu_info, indent=2, default=str))


def test_pid_lookup():
    """Test filtering processes by a specific PID (simulates job monitor use case)."""
    print("\n=== PID LOOKUP TEST ===\n")

    plugin = NvidiaMonitorPlugin()
    stats = plugin.execute("get_system_status")

    details = stats.get('details', {})
    processes = details.get('processes', [])

    if not processes:
        print("No GPU processes to test PID lookup against.")
        return

    # Pick the first process as a test target
    target_pid = processes[0]['pid']
    print(f"Looking up PID {target_pid}...")

    matching = [p for p in processes if p['pid'] == target_pid]
    print(f"Found {len(matching)} entries for PID {target_pid}:")
    for m in matching:
        print(f"  GPU {m['gpu_index']}: {m['gpu_memory_mb']}MB")

    print(f"\nThis is how the job monitor service will filter by worker PID.")


if __name__ == "__main__":
    test_system_stats()
    test_raw_gpu_info()
    test_pid_lookup()
    print("\n=== ALL TESTS COMPLETE ===")
