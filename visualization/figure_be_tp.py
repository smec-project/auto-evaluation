import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob


def load_ue_data(directory):
    """Load UE data from a directory containing latency_ue*.txt files"""
    data_files = glob.glob(os.path.join(directory, "latency_*.txt"))
    data_files.sort()  # Sort to ensure consistent ordering

    print(f"Found {len(data_files)} UE data files in {directory}:")
    for i, file in enumerate(data_files):
        print(f"  UE{i+1}: {os.path.basename(file)}")

    # Read all data files and find time intersection
    all_data = {}
    all_times = []

    for i, file in enumerate(data_files):
        ue_id = i + 1
        try:
            # Read the data file with tab separator
            df = pd.read_csv(file, sep="\t")

            # Extract time and throughput
            times = df["Time"].values
            throughput_mbps = (
                df["Throughput"].values * 8
            )  # Convert MBps to Mbps (like reference)

            all_data[f"UE{ue_id}"] = {
                "times": times,
                "throughput": throughput_mbps,
            }
            all_times.extend(times)

            print(
                f"  UE{ue_id}: Time range {times[0]:.1f}s to {times[-1]:.1f}s,"
                f" {len(times)} data points"
            )

        except Exception as e:
            print(f"  Error processing UE{ue_id} file {file}: {e}")
            continue

    if not all_data:
        return None, None, None

    # Set fixed time range: 50s to 300s (250 seconds)
    min_start_time = 50.0
    max_end_time = 300.0

    print(
        f"  Using fixed time range: {min_start_time:.1f}s to"
        f" {max_end_time:.1f}s"
    )

    return all_data, min_start_time, max_end_time


def plot_workload_data(
    ax,
    all_data,
    min_start_time,
    max_end_time,
    colors,
    line_styles,
    workload_name,
    show_ylabel=True,
    y_range=(0, 4),
):
    """Plot data for a specific workload on the given axis"""
    # Process each UE and plot within the intersection time range
    handles = []
    labels = []

    for i, (ue_name, data) in enumerate(all_data.items()):
        times = data["times"]
        throughput = data["throughput"]

        # Filter data within the intersection time range
        mask = (times >= min_start_time) & (times <= max_end_time)
        filtered_times = times[mask]
        filtered_throughput = throughput[mask]

        # Normalize time axis to start from 0
        normalized_times = filtered_times - min_start_time

        # Plot the data with enhanced styling to match CDF plot
        if len(normalized_times) > 0:
            line = ax.plot(
                normalized_times,
                filtered_throughput,
                color=colors[i % len(colors)],
                linestyle=line_styles[i % len(line_styles)],
                linewidth=6,
                marker="o",
                markersize=12,
                alpha=0.9,
                label=ue_name,
                markerfacecolor="white",
                markeredgewidth=3,
                markeredgecolor=colors[i % len(colors)],
            )

            handles.extend(line)
            labels.append(ue_name)

            print(
                f"  {ue_name}: {len(normalized_times)} data points in"
                " intersection, normalized time 0s to"
                f" {normalized_times[-1]:.1f}s"
            )

    # Configure the subplot with enhanced styling
    ax.set_xlabel("Time (s)", fontsize=54, color="#333333")
    if show_ylabel:
        ax.set_ylabel("Throughput (Mbps)", fontsize=54, color="#333333")

    # Enhanced grid
    ax.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")
    ax.set_axisbelow(True)

    # Set axis limits
    ax.set_xlim(left=0)
    ax.set_ylim(y_range[0], y_range[1])

    # Set custom x-axis ticks starting from 100 to avoid overlapping with y-axis 0
    import matplotlib.ticker as ticker

    x_max = ax.get_xlim()[1]
    x_ticks = np.arange(
        100, int(x_max) + 1, 100
    )  # 100, 200, etc. only up to actual data range
    if len(x_ticks) == 0:  # Fallback
        x_ticks = [100, 200]
    ax.set_xticks(x_ticks)

    # Enhanced tick formatting to match CDF plot
    ax.tick_params(
        axis="x",
        which="major",
        labelsize=54,
        colors="#333333",
        width=2,
        length=10,
    )
    ax.tick_params(
        axis="y",
        which="major",
        labelsize=54,
        colors="#333333",
        width=2,
        length=10,
    )

    # Add subtle background color
    ax.set_facecolor("#fafafa")

    # Enhance the border to match CDF plot
    for spine in ax.spines.values():
        spine.set_linewidth(2.5)
        spine.set_color("#333333")

    return handles, labels


def generate_figure_17(results_base_path, output_dir):
    """
    Generate Figure 17: BE throughput timeline comparison between steady and dynamic workloads

    Args:
        results_base_path (str): Base path to results directory
        output_dir (str): Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Set up the plot with two subplots side by side
    plt.style.use("default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 8))

    # Softer color palette
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E", "#7209B7"]
    line_styles = ["-", "--", "-.", ":", "-", "--"]

    # Define the two workload directories
    steady_dir = os.path.join(
        results_base_path, "smec_all_tasks", "file-transfer", "server"
    )
    dynamic_dir = os.path.join(
        results_base_path, "smec_all_tasks_dynamic", "file-transfer", "server"
    )

    # Load and plot steady workload data (left subplot)
    print("Processing Steady Workload:")
    steady_data, steady_min_start, steady_max_end = load_ue_data(steady_dir)
    if steady_data:
        handles1, labels1 = plot_workload_data(
            ax1,
            steady_data,
            steady_min_start,
            steady_max_end,
            colors,
            line_styles,
            "steady",
            show_ylabel=True,
            y_range=(0, 3),
        )

    # Load and plot dynamic workload data (right subplot)
    print("\nProcessing Dynamic Workload:")
    dynamic_data, dynamic_min_start, dynamic_max_end = load_ue_data(dynamic_dir)
    if dynamic_data:
        handles2, labels2 = plot_workload_data(
            ax2,
            dynamic_data,
            dynamic_min_start,
            dynamic_max_end,
            colors,
            line_styles,
            "dynamic",
            show_ylabel=False,
            y_range=(1, 4),
        )

    # Create shared legend above the plots
    if steady_data:
        fig.legend(
            handles1,
            labels1,
            fontsize=44,
            frameon=True,
            fancybox=True,
            shadow=True,
            bbox_to_anchor=(0.5, 1.05),
            loc="upper center",
            ncol=6,
            framealpha=0.95,
            edgecolor="#333333",
            facecolor="white",
        )

    # Adjust layout to make room for the legend
    plt.tight_layout()
    plt.subplots_adjust(top=0.82)  # Make room for legend above

    # Save the plot (PDF only)
    output_path_pdf = os.path.join(output_dir, "figure_17.pdf")
    plt.savefig(
        output_path_pdf, dpi=300, bbox_inches="tight", facecolor="white"
    )

    print(f"\nFigure 17 saved as:")
    print(f"  - {output_path_pdf}")

    plt.close()


def main():
    """
    Main function to create BE throughput timeline comparison
    """
    # Set base path to results directory
    base_path = "results"
    output_dir = "figures"

    print(f"=== BE Throughput Timeline Analysis (Figure 17) ===")
    print(f"Base path: {base_path}")
    print(f"Output directory: {output_dir}")

    if not os.path.exists(base_path):
        print(f"Base path {base_path} does not exist!")
        return

    try:
        # Generate Figure 17
        generate_figure_17(base_path, output_dir)
        print(
            "\nBE throughput timeline plot with dual workloads has been"
            " generated!"
        )

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
