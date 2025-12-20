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


def main():
    parser = argparse.ArgumentParser(description="Auto Evaluation Tool")
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        required=True,
        choices=["data"],
        help="Operation mode: data",
    )

    args = parser.parse_args()

    if args.mode == "data":
        data_mode()


if __name__ == "__main__":
    main()
