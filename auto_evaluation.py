import argparse
import sys
from time import sleep
from datetime import datetime
from src.run_experiment import run_experiment as run_experiment_base
from src.host_manager import HostManager
from src.get_results import (
    get_ran_logs,
    get_scheduler_logs,
    get_server_results,
    get_client_results,
)
from src.get_results import clean_results
from src.preprocess_results import (
    preprocess_smec_results,
    preprocess_scheduler_logs,
)
from visualization.figure_reproduce_static import (
    generate_figure_9,
    generate_figure_10,
    generate_figure_11,
    generate_figure_12,
)
from visualization.figure_reproduce_dynamic import (
    generate_figure_13,
    generate_figure_14,
    generate_figure_15,
    generate_figure_16,
)
from visualization.figure_be_tp import (
    generate_figure_17,
)
from visualization.figure_microbench import (
    generate_figure_18_a,
    generate_figure_18_b,
    generate_figure_21,
)
from visualization.figure_accuracy import (
    generate_figure_20_a,
    generate_figure_19,
    generate_figure_20_b,
)

TRACE_FILE = "trace.log"


def _load_trace(trace_path: str = TRACE_FILE):
    trace = {}
    try:
        with open(trace_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    key = f"{parts[0]}|{parts[1]}"
                    trace[key] = parts[2]
    except FileNotFoundError:
        pass
    return trace


def _append_trace(
    config_file: str, operation: int, status: str, trace_path: str = TRACE_FILE
):
    timestamp = datetime.now().isoformat(timespec="seconds")
    with open(trace_path, "a", encoding="utf-8") as f:
        f.write(f"{config_file}|{operation}|{status}|{timestamp}\n")


def run_experiment(
    config_file: str,
    operation: int,
    cleanup_before: bool = True,
    trace_path: str = TRACE_FILE,
):
    """
    Wrapper with trace/resume and optional pre-cleanup.
    Skips already successful (config, operation) pairs recorded in trace.
    """
    key = f"{config_file}|{operation}"
    trace = _load_trace(trace_path)
    if key in trace and trace[key].startswith("SUCCESS"):
        print(f"[trace] skip completed: {key}")
        return 0

    if cleanup_before and operation not in (1, 3):
        print(f"[trace] pre-cleanup before {key}")
        run_experiment_base(config_file, 1)

    status = run_experiment_base(config_file, operation)
    status_str = "SUCCESS" if status == 0 else f"FAIL:{status}"
    _append_trace(config_file, operation, status_str, trace_path)
    return status


def data_mode():
    """Handle data mode logic"""
    print("Running in data mode...")

    # Run evaluation on smec_all_tasks.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_ran_logs("results/smec_all_tasks")
    get_scheduler_logs("results/smec_all_tasks")
    get_server_results("results/smec_all_tasks", "smec")
    get_client_results("results/smec_all_tasks", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_rtt.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_rtt.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_rtt", "smec")
    get_client_results("results/smec_all_tasks_rtt", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_disable.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_disable.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_disable", "smec")
    get_client_results("results/smec_all_tasks_disable", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_wo_drop.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_wo_drop.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_wo_drop", "smec")
    get_client_results("results/smec_all_tasks_wo_drop", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_disable_32cpu.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_disable_32cpu.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_scheduler_logs("results/smec_all_tasks_disable_32cpu")
    get_server_results("results/smec_all_tasks_disable_32cpu", "smec")
    get_client_results("results/smec_all_tasks_disable_32cpu", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_dynamic.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_dynamic.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_ran_logs("results/smec_all_tasks_dynamic")
    get_scheduler_logs("results/smec_all_tasks_dynamic")
    get_server_results("results/smec_all_tasks_dynamic", "smec")
    get_client_results("results/smec_all_tasks_dynamic", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_dynamic_rtt.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_dynamic_rtt.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_dynamic_rtt", "smec")
    get_client_results("results/smec_all_tasks_dynamic_rtt", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_dynamic_disable.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_dynamic_disable.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_dynamic_disable", "smec")
    get_client_results("results/smec_all_tasks_dynamic_disable", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_dynamic_wo_drop.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_dynamic_wo_drop.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/smec_all_tasks_dynamic_wo_drop", "smec")
    get_client_results("results/smec_all_tasks_dynamic_wo_drop", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on smec_all_tasks_dynamic_disable_32cpu.json with operation mode 0 (Full deploy)
    config_file = "config/smec_all_tasks_dynamic_disable_32cpu.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_scheduler_logs("results/smec_all_tasks_dynamic_disable_32cpu")
    get_server_results("results/smec_all_tasks_dynamic_disable_32cpu", "smec")
    get_client_results("results/smec_all_tasks_dynamic_disable_32cpu", "smec")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on default_all_tasks.json with operation mode 0 (Full deploy)
    config_file = "config/default_all_tasks.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/default_all_tasks", "default")
    get_client_results("results/default_all_tasks", "default")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on default_all_tasks_dynamic.json with operation mode 0 (Full deploy)
    config_file = "config/default_all_tasks_dynamic.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/default_all_tasks_dynamic", "default")
    get_client_results("results/default_all_tasks_dynamic", "default")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on tutti_all_tasks.json with operation mode 0 (Full deploy)
    config_file = "config/tutti_all_tasks.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/tutti_all_tasks", "tutti")
    get_client_results("results/tutti_all_tasks", "tutti")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on tutti_all_tasks_dynamic.json with operation mode 0 (Full deploy)
    config_file = "config/tutti_all_tasks_dynamic.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/tutti_all_tasks_dynamic", "tutti")
    get_client_results("results/tutti_all_tasks_dynamic", "tutti")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on arma_all_tasks.json with operation mode 0 (Full deploy)
    config_file = "config/arma_all_tasks.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/arma_all_tasks", "arma")
    get_client_results("results/arma_all_tasks", "arma")
    clean_results()
    exit_code = run_experiment(config_file, 3)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")

    # Run evaluation on arma_all_tasks_dynamic.json with operation mode 0 (Full deploy)
    config_file = "config/arma_all_tasks_dynamic.json"
    print(f"Running experiment with config: {config_file}")
    exit_code = run_experiment(config_file, 2)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)
    get_server_results("results/arma_all_tasks_dynamic", "arma")
    get_client_results("results/arma_all_tasks_dynamic", "arma")
    clean_results()
    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")


def preprocess_mode():
    """Handle preprocess mode logic - preprocess SMEC results"""
    print("Running in preprocess mode...")

    # List of SMEC result directories that need controller.log preprocessing
    smec_dirs = [
        "results/smec_all_tasks",
        "results/smec_all_tasks_dynamic",
    ]

    print("\n" + "=" * 60)
    print("PART 1: Processing Controller Logs (Remaining Time)")
    print("=" * 60)

    for results_dir in smec_dirs:
        print(f"\n{'='*60}")
        print(f"Processing: {results_dir}")
        print(f"{'='*60}")
        preprocess_smec_results(results_dir)

    # List of directories that need scheduler.log preprocessing
    scheduler_dirs = [
        "results/smec_all_tasks_disable_32cpu",
        "results/smec_all_tasks_dynamic_disable_32cpu",
    ]

    print("\n" + "=" * 60)
    print("PART 2: Processing Scheduler Logs (Waiting/Processing Time)")
    print("=" * 60)

    for results_dir in scheduler_dirs:
        print(f"\n{'='*60}")
        print(f"Processing: {results_dir}")
        print(f"{'='*60}")
        preprocess_scheduler_logs(results_dir)

    print("\n" + "=" * 60)
    print("All preprocessing complete!")
    print("=" * 60)


def figures_mode():
    """Handle figures mode logic - generate all paper figures"""
    print("Running in figures mode...")

    # Define base paths
    results_base_path = "results"
    output_dir = "figures"

    # Generate Figure 9
    print("\n=== Generating Figure 9 ===")
    generate_figure_9(results_base_path, output_dir)
    print("\nFigure 9 generated successfully!")

    # Generate Figure 10
    print("\n=== Generating Figure 10 ===")
    generate_figure_10(results_base_path, output_dir)
    print("\nFigure 10 generated successfully!")

    # Generate Figure 11
    print("\n=== Generating Figure 11 ===")
    generate_figure_11(results_base_path, output_dir)
    print("\nFigure 11 generated successfully!")

    # Generate Figure 12
    print("\n=== Generating Figure 12 ===")
    generate_figure_12(results_base_path, output_dir)
    print("\nFigure 12 generated successfully!")

    # Generate Figure 13
    print("\n=== Generating Figure 13 ===")
    generate_figure_13(results_base_path, output_dir)
    print("\nFigure 13 generated successfully!")

    # Generate Figure 14
    print("\n=== Generating Figure 14 ===")
    generate_figure_14(results_base_path, output_dir)
    print("\nFigure 14 generated successfully!")

    # Generate Figure 15
    print("\n=== Generating Figure 15 ===")
    generate_figure_15(results_base_path, output_dir)
    print("\nFigure 15 generated successfully!")

    # Generate Figure 16
    print("\n=== Generating Figure 16 ===")
    generate_figure_16(results_base_path, output_dir)
    print("\nFigure 16 generated successfully!")

    # Generate Figure 17
    print("\n=== Generating Figure 17 ===")
    generate_figure_17(results_base_path, output_dir)
    print("\nFigure 17 generated successfully!")

    # Generate Figure 18a
    print("\n=== Generating Figure 18a ===")
    generate_figure_18_a(results_base_path, output_dir)
    print("\nFigure 18a generated successfully!")

    # Generate Figure 18b
    print("\n=== Generating Figure 18b ===")
    generate_figure_18_b(results_base_path, output_dir)
    print("\nFigure 18b generated successfully!")

    # Generate Figure 19
    print("\n=== Generating Figure 19 ===")
    generate_figure_19(results_base_path, output_dir)
    print("\nFigure 19 generated successfully!")

    # Generate Figure 20a
    print("\n=== Generating Figure 20a ===")
    generate_figure_20_a(results_base_path, output_dir)
    print("\nFigure 20a generated successfully!")

    # Generate Figure 20b
    print("\n=== Generating Figure 20b ===")
    generate_figure_20_b(results_base_path, output_dir)
    print("\nFigure 20b generated successfully!")

    # Generate Figure 21
    print("\n=== Generating Figure 21 ===")
    generate_figure_21(results_base_path, output_dir)
    print("\nFigure 21 generated successfully!")


def test_mode():
    """Test SSH connectivity to all configured hosts."""
    print("Running in test mode (SSH connection test)...")
    manager = HostManager("hosts_config.yaml")
    results = manager.test_connections()

    all_ok = True
    for host, ok in results.items():
        status = "OK" if ok else "FAIL"
        print(f"{host}: {status}")
        all_ok = all_ok and ok

    if not all_ok:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Auto Evaluation Tool")
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        required=True,
        choices=["data", "figures", "preprocess", "test"],
        help="Operation mode: data | figures | preprocess | test",
    )

    args = parser.parse_args()

    if args.mode == "data":
        data_mode()
    elif args.mode == "figures":
        figures_mode()
    elif args.mode == "preprocess":
        preprocess_mode()
    elif args.mode == "test":
        test_mode()


if __name__ == "__main__":
    main()
