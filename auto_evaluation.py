import argparse
import os
import shutil
import sys
from time import sleep
from typing import Optional
from src.run_experiment import run_experiment
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


def run_experiment_group(
    config_file: str,
    exp_type: str,
    fetch_ran_logs: bool,
    fetch_scheduler_logs: bool,
):
    """
    Run one experiment config with optional log collection.
    fetch_ran_logs: fetch ran logs if True.
    fetch_scheduler_logs: fetch scheduler logs if True.
    """
    results_dir = (
        f"results/{os.path.splitext(os.path.basename(config_file))[0]}"
    )

    exit_code = run_experiment(config_file, 0)
    if exit_code == 0:
        print("Experiment completed successfully!")
    else:
        print(f"Experiment failed with exit code: {exit_code}")
    sleep(420)

    if fetch_ran_logs:
        get_ran_logs(results_dir)
    if fetch_scheduler_logs:
        get_scheduler_logs(results_dir)

    get_server_results(results_dir, exp_type)
    get_client_results(results_dir, exp_type)
    clean_results()

    exit_code = run_experiment(config_file, 1)
    if exit_code == 0:
        print("Cleanup completed successfully!")
    else:
        print(f"Cleanup failed with exit code: {exit_code}")


def data_mode(selected_config: Optional[str] = None):
    """Handle data mode logic"""
    print("Running in data mode...")

    # special pre-cleanup for the base SMEC config (only when relevant)
    smec_base = "config/smec_all_tasks.json"
    if selected_config is None or selected_config == smec_base:
        print(f"Pre-cleanup for {smec_base}")
        pre_exit = run_experiment(smec_base, 1)
        if pre_exit == 0:
            print("Pre-cleanup completed successfully!")
        else:
            print(f"Pre-cleanup failed with exit code: {pre_exit}")
        sleep(5)

    experiments = [
        (smec_base, "smec", True, True),
        ("config/smec_all_tasks_rtt.json", "smec", False, False),
        ("config/smec_all_tasks_disable.json", "smec", False, False),
        ("config/smec_all_tasks_wo_drop.json", "smec", False, False),
        ("config/smec_all_tasks_disable_32cpu.json", "smec", False, True),
        ("config/smec_all_tasks_dynamic.json", "smec", True, True),
        ("config/smec_all_tasks_dynamic_rtt.json", "smec", False, False),
        ("config/smec_all_tasks_dynamic_disable.json", "smec", False, False),
        ("config/smec_all_tasks_dynamic_wo_drop.json", "smec", False, False),
        (
            "config/smec_all_tasks_dynamic_disable_32cpu.json",
            "smec",
            False,
            True,
        ),
        ("config/default_all_tasks.json", "default", False, False),
        ("config/default_all_tasks_dynamic.json", "default", False, False),
        ("config/tutti_all_tasks.json", "tutti", False, False),
        ("config/tutti_all_tasks_dynamic.json", "tutti", False, False),
        ("config/arma_all_tasks.json", "arma", False, False),
        ("config/arma_all_tasks_dynamic.json", "arma", False, False),
    ]

    if selected_config:
        experiments = [
            item for item in experiments if item[0] == selected_config
        ]
        if not experiments:
            print(f"Config not found: {selected_config}")
            sys.exit(1)

    for config_file, exp_type, fetch_ran, fetch_scheduler in experiments:
        print(f"\nRunning experiment with config: {config_file}")
        run_experiment_group(config_file, exp_type, fetch_ran, fetch_scheduler)


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


def figures_mode(target_figure: Optional[str] = None):
    """Handle figures mode logic - generate all paper figures"""
    print("Running in figures mode...")

    # Define base paths
    results_base_path = "results"
    output_dir = "figures"

    figures = [
        ("9", generate_figure_9, "Figure 9"),
        ("10", generate_figure_10, "Figure 10"),
        ("11", generate_figure_11, "Figure 11"),
        ("12", generate_figure_12, "Figure 12"),
        ("13", generate_figure_13, "Figure 13"),
        ("14", generate_figure_14, "Figure 14"),
        ("15", generate_figure_15, "Figure 15"),
        ("16", generate_figure_16, "Figure 16"),
        ("17", generate_figure_17, "Figure 17"),
        ("18a", generate_figure_18_a, "Figure 18a"),
        ("18b", generate_figure_18_b, "Figure 18b"),
        ("19", generate_figure_19, "Figure 19"),
        ("20a", generate_figure_20_a, "Figure 20a"),
        ("20b", generate_figure_20_b, "Figure 20b"),
        ("21", generate_figure_21, "Figure 21"),
    ]

    if target_figure:
        key = target_figure.lower()
        figures = [item for item in figures if item[0] == key]
        if not figures:
            print(f"Figure not found: {target_figure}")
            sys.exit(1)

    for _, func, label in figures:
        print(f"\n=== Generating {label} ===")
        func(results_base_path, output_dir)
        print(f"\n{label} generated successfully!")


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


def clean_mode(selected_config: Optional[str] = None):
    """Remove generated results; if no config specified, also remove figures."""
    print("Running in clean mode...")
    if selected_config:
        results_dir = (
            f"results/{os.path.splitext(os.path.basename(selected_config))[0]}"
        )
        targets = [results_dir]
    else:
        targets = ["results", "figures"]

    for path in targets:
        if os.path.exists(path):
            print(f"Removing: {path}")
            try:
                shutil.rmtree(path)
                print(f"Removed: {path}")
            except OSError as e:
                print(f"Failed to remove {path}: {e}")
        else:
            print(f"Skip missing: {path}")


def main():
    parser = argparse.ArgumentParser(description="Auto Evaluation Tool")
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        required=True,
        choices=["data", "figures", "preprocess", "test", "clean"],
        help="Operation mode: data | figures | preprocess | test | clean",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        required=False,
        help=(
            "Optional: only run the specified config file in data mode; if used"
            " with clean mode, only clean that config's results directory"
        ),
    )
    parser.add_argument(
        "-f",
        "--figure",
        type=str,
        required=False,
        help=(
            "Optional: only generate the specified figure id (e.g., 9, 10, 18a,"
            " 20b)"
        ),
    )

    args = parser.parse_args()

    if args.mode == "data":
        data_mode(args.config_file)
    elif args.mode == "figures":
        figures_mode(args.figure)
    elif args.mode == "preprocess":
        preprocess_mode()
    elif args.mode == "test":
        test_mode()
    elif args.mode == "clean":
        clean_mode(args.config_file)


if __name__ == "__main__":
    main()
