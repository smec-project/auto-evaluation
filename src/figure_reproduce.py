import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob


def read_e2e_latency_data(directory_path, skip_lines=100, skip_tail=5):
    """
    Read E2E latency data from client directory

    Args:
        directory_path (str): Path to the client directory containing latency files
        skip_lines (int): Number of lines to skip from the beginning of each file
        skip_tail (int): Number of lines to skip from the end of each file

    Returns:
        list: Combined latency data from all files in the directory
    """
    all_data = []

    # Find all .txt files in the directory
    file_pattern = os.path.join(directory_path, "*.txt")
    files = glob.glob(file_pattern)

    print(f"Processing {len(files)} files in {directory_path}")

    for file_path in files:
        try:
            # Read the file, skipping the first skip_lines lines
            df = pd.read_csv(file_path, sep=r"\s+", skiprows=skip_lines)

            # Extract the E2E latency column (second column)
            if len(df.columns) >= 2:
                latency_column = df.iloc[
                    :, 1
                ]  # Get the second column (E2E latency)

                # Convert to string first, then extract numeric values
                latency_strings = latency_column.astype(str)

                # Extract numeric values by removing 'ms' suffix and converting to float
                latency_values = []
                for value in latency_strings:
                    try:
                        # Remove 'ms' if present and convert to float
                        numeric_value = float(value.replace("ms", "").strip())
                        latency_values.append(numeric_value)
                    except (ValueError, AttributeError):
                        # Skip invalid values
                        continue

                # Skip the last skip_tail data points
                if len(latency_values) > skip_tail:
                    latency_values = latency_values[:-skip_tail]

                # Add to our combined data
                all_data.extend(latency_values)

                print(
                    f"  - {os.path.basename(file_path)}:"
                    f" {len(latency_values)} data points (after skipping head"
                    " and tail)"
                )
            else:
                print(
                    f"  - {os.path.basename(file_path)}: Unexpected format,"
                    " skipped"
                )

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return all_data


def calculate_cdf(data):
    """
    Calculate CDF (Cumulative Distribution Function) for the given data

    Args:
        data (list): List of numerical values

    Returns:
        tuple: (sorted_data, cdf_values)
    """
    # Sort the data
    sorted_data = np.sort(data)

    # Calculate CDF values
    n = len(sorted_data)
    cdf_values = np.arange(1, n + 1) / n

    return sorted_data, cdf_values


def generate_figure_10(results_base_path, output_dir):
    """
    Generate Figure 10: Combined CDF plot for E2E latency across applications

    Args:
        results_base_path (str): Base path to results directory
        output_dir (str): Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define SLO thresholds for different applications
    slo_thresholds = {
        "video-transcoding": 100.0,
        "video-od": 100.0,
        "video-sr": 150.0,
    }

    print(f"Using SLO thresholds: {slo_thresholds}")

    # Define applications and their display names
    applications = {
        "video-transcoding": "SS",
        "video-od": "AR",
        "video-sr": "VC",
    }

    # Map scheduler directories to their names
    scheduler_mapping = {
        "default_all_tasks": "default",
        "tutti_all_tasks": "tutti",
        "smec_all_tasks": "smec",
        "arma_all_tasks": "arma",
    }

    # Process data for each application
    app_data = {}

    for app_dir, app_name in applications.items():
        print(f"\n=== Processing application: {app_name} ({app_dir}) ===")
        app_data[app_dir] = {}

        for scheduler_dir, scheduler_name in scheduler_mapping.items():
            # Construct path to client directory
            client_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "client"
            )

            if os.path.exists(client_path):
                print(f"\nProcessing {scheduler_dir}/{app_dir}/client")
                data = read_e2e_latency_data(
                    client_path, skip_lines=100, skip_tail=5
                )

                if len(data) > 0:
                    app_data[app_dir][scheduler_name] = data
                    print(
                        f"Total data points for {scheduler_name}: {len(data)}"
                    )

                    # Print statistics
                    print(f"\nStatistics for {app_name} - {scheduler_name}:")
                    print(f"  - Mean: {np.mean(data):.2f} ms")
                    print(f"  - Median: {np.median(data):.2f} ms")
                    print(
                        f"  - 95th percentile: {np.percentile(data, 95):.2f} ms"
                    )
                    print(
                        f"  - 99th percentile: {np.percentile(data, 99):.2f} ms"
                    )
            else:
                print(f"Client directory not found: {client_path}")

    # Create subplots for each application
    fig, axes = plt.subplots(1, 3, figsize=(21, 6.5), sharey=True)

    # Try to use seaborn style
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    # Enhanced colors and styles for each scheduler
    plot_configs = {
        "default": {
            "color": "#1f77b4",
            "linestyle": "-",
            "marker": "o",
            "markevery": 400,
        },  # solid blue
        "tutti": {
            "color": "#9467bd",
            "linestyle": ":",
            "marker": "v",
            "markevery": 400,
        },  # dotted purple
        "smec": {
            "color": "#ff7f0e",
            "linestyle": "--",
            "marker": "s",
            "markevery": 400,
        },  # dashed orange
        "arma": {
            "color": "#2ca02c",
            "linestyle": "-.",
            "marker": "^",
            "markevery": 400,
        },  # dash-dot green
    }

    # Legend labels
    legend_labels = {
        "default": "Default",
        "tutti": "Tutti",
        "smec": "SMEC",
        "arma": "ARMA",
    }

    # Plot for each application
    for idx, (app_dir, app_name) in enumerate(applications.items()):
        ax = axes[idx]

        if app_dir in app_data and len(app_data[app_dir]) > 0:
            # Plot each scheduler for this application
            for scheduler, data in app_data[app_dir].items():
                if len(data) > 0:
                    # Calculate CDF
                    sorted_data, cdf_values = calculate_cdf(data)

                    # Plot CDF curve
                    legend_label = legend_labels.get(scheduler, scheduler)

                    ax.plot(
                        sorted_data,
                        cdf_values,
                        color=plot_configs[scheduler]["color"],
                        linestyle=plot_configs[scheduler]["linestyle"],
                        linewidth=6,
                        label=legend_label,
                        alpha=0.9,
                        marker=plot_configs[scheduler]["marker"],
                        markevery=plot_configs[scheduler]["markevery"],
                        markersize=12,
                        markerfacecolor="white",
                        markeredgewidth=3,
                        markeredgecolor=plot_configs[scheduler]["color"],
                    )

            # Add SLO line for this subplot
            slo_value = slo_thresholds.get(app_dir, 100.0)
            ax.axvline(
                x=slo_value,
                color="#d62728",
                linestyle=":",
                linewidth=8,
                alpha=0.8,
                zorder=5,
            )

        # Customize each subplot
        ax.set_xlabel(f"{app_name}", fontsize=52, color="#333333")

        # Set axis properties
        ax.set_ylim(0, 1.05)
        ax.set_xscale("log")
        ax.set_xlim(left=30)

        # Grid styling
        ax.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")

        # Tick styling
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=52,
            colors="#333333",
            width=2,
            length=8,
        )

        # Background color
        ax.set_facecolor("#fafafa")

        # Border styling
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
            spine.set_color("#333333")

        # Set custom ticks
        import matplotlib.ticker as ticker

        ax.yaxis.set_major_locator(ticker.FixedLocator([0, 0.5, 1.0]))
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=6))
        ax.xaxis.set_minor_locator(
            ticker.LogLocator(base=10, subs=(0.2, 0.4, 0.6, 0.8), numticks=12)
        )

    # Set y-axis label only for the leftmost subplot
    axes[0].set_ylabel("CDF", fontsize=52, color="#333333")

    # Create a single shared legend
    handles, labels = axes[0].get_legend_handles_labels()

    # Add SLO to legend
    slo_line = plt.Line2D(
        [0], [0], color="#d62728", linestyle=":", linewidth=8, alpha=0.8
    )
    handles.append(slo_line)
    labels.append("SLO")

    # Place legend at the top center of the entire figure
    fig.legend(
        handles,
        labels,
        fontsize=47,
        frameon=True,
        fancybox=True,
        shadow=True,
        bbox_to_anchor=(0.53, 1.08),
        loc="center",
        ncol=5,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
        columnspacing=0.8,
        handletextpad=0.3,
    )

    # Adjust layout
    plt.tight_layout()

    # Save the plot
    output_path = os.path.join(output_dir, "figure_10.pdf")
    plt.savefig(output_path, bbox_inches="tight")

    print(f"\nFigure 10 saved as '{output_path}'")
    plt.close()
