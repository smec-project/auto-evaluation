import argparse
from time import sleep
from src.run_experiment import run_experiment
from src.get_results import (
    get_ran_logs,
    get_scheduler_logs,
    get_server_results,
    get_client_results,
)
from src.get_results import clean_results
from src.figure_reproduce_static import (
    generate_figure_9,
    generate_figure_10,
    generate_figure_11,
    generate_figure_12,
)
from src.figure_reproduce_dynamic import (
    generate_figure_13,
    generate_figure_14,
    generate_figure_15,
    generate_figure_16,
)


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


def figures_mode():
    """Handle figures mode logic - generate all paper figures"""
    print("Running in figures mode...")

    # Define base paths
    results_base_path = "results"
    output_dir = "figures"

    # # Generate Figure 9
    # print("\n=== Generating Figure 9 ===")
    # generate_figure_9(results_base_path, output_dir)

    # # Generate Figure 10
    # print("\n=== Generating Figure 10 ===")
    # generate_figure_10(results_base_path, output_dir)

    # # Generate Figure 11
    # print("\n=== Generating Figure 11 ===")
    # generate_figure_11(results_base_path, output_dir)

    # # Generate Figure 12
    # print("\n=== Generating Figure 12 ===")
    # generate_figure_12(results_base_path, output_dir)

    # # Generate Figure 13
    # print("\n=== Generating Figure 13 ===")
    # generate_figure_13(results_base_path, output_dir)

    # # Generate Figure 14
    # print("\n=== Generating Figure 14 ===")
    # generate_figure_14(results_base_path, output_dir)

    # Generate Figure 15
    print("\n=== Generating Figure 15 ===")
    generate_figure_15(results_base_path, output_dir)

    # Generate Figure 16
    print("\n=== Generating Figure 16 ===")
    generate_figure_16(results_base_path, output_dir)
    print("\nAll figures generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Auto Evaluation Tool")
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        required=True,
        choices=["data", "figures"],
        help="Operation mode: data | figures",
    )

    args = parser.parse_args()

    if args.mode == "data":
        data_mode()
    elif args.mode == "figures":
        figures_mode()


if __name__ == "__main__":
    main()
