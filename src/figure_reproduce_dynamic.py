import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import re


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


def generate_figure_14(results_base_path, output_dir):
    """
    Generate Figure 14: Combined CDF plot for E2E latency across applications

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
        "default_all_tasks_dynamic": "default",
        "tutti_all_tasks_dynamic": "tutti",
        "smec_all_tasks_dynamic": "smec",
        "arma_all_tasks_dynamic": "arma",
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
    output_path = os.path.join(output_dir, "figure_14.pdf")
    plt.savefig(output_path, bbox_inches="tight")

    print(f"\nFigure 14 saved as '{output_path}'")
    plt.close()


def read_latency_data_with_slo(
    directory_path, slo_threshold, skip_lines=100, skip_tail=5
):
    """
    Read E2E latency data and calculate SLO satisfaction

    Args:
        directory_path (str): Path to the directory containing latency files
        slo_threshold (float): SLO threshold in milliseconds
        skip_lines (int): Number of lines to skip from the beginning of each file
        skip_tail (int): Number of lines to skip from the end of each file

    Returns:
        tuple: (all_latencies, total_frames, satisfied_frames) for SLO analysis
    """
    all_latencies = []
    total_frames = 0
    satisfied_frames = 0

    # Find all .txt files in the directory
    file_pattern = os.path.join(directory_path, "*.txt")
    files = glob.glob(file_pattern)

    print(f"  Processing {len(files)} files in {directory_path}")

    for file_path in files:
        try:
            # Read the file, skipping the first skip_lines lines
            df = pd.read_csv(file_path, sep=r"\s+", skiprows=skip_lines)

            # Extract frame indices and E2E latency values
            if len(df.columns) >= 2:
                frame_column = df.iloc[:, 0]  # Frame indices
                latency_column = df.iloc[:, 1]  # E2E latency values

                # Convert latency to numeric values
                latency_strings = latency_column.astype(str)
                latency_values = []

                for value in latency_strings:
                    try:
                        # Remove 'ms' if present and convert to float
                        numeric_value = float(value.replace("ms", "").strip())
                        latency_values.append(numeric_value)
                    except (ValueError, AttributeError):
                        continue

                # Skip the last skip_tail data points
                if len(latency_values) > skip_tail:
                    latency_values = latency_values[:-skip_tail]

                # Calculate frame statistics for this file
                if len(latency_values) > 0:
                    # Convert frame indices to numeric values
                    frame_indices = []
                    for idx in frame_column:
                        try:
                            frame_indices.append(int(idx))
                        except (ValueError, TypeError):
                            continue

                    # Skip the last skip_tail frame indices
                    if len(frame_indices) > skip_tail:
                        frame_indices = frame_indices[:-skip_tail]

                    if len(frame_indices) > 0:
                        # Calculate total frames as max_index - min_index + 1
                        min_frame = min(frame_indices)
                        max_frame = max(frame_indices)
                        file_total_frames = max_frame - min_frame + 1
                        file_satisfied_frames = sum(
                            1 for lat in latency_values if lat <= slo_threshold
                        )

                        # Add to overall statistics
                        all_latencies.extend(latency_values)
                        total_frames += file_total_frames
                        satisfied_frames += file_satisfied_frames

                        print(
                            f"    - {os.path.basename(file_path)}:"
                            f" {file_total_frames} frames, "
                            f"{file_satisfied_frames} satisfied "
                            f"({file_satisfied_frames/len(latency_values)*100:.1f}%)"
                        )
        except Exception as e:
            print(f"    Error reading {file_path}: {e}")

    return all_latencies, total_frames, satisfied_frames


def generate_figure_13(results_base_path, output_dir):
    """
    Generate Figure 13: SLO satisfaction rate comparison across applications

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

    # Define applications and their display names
    applications = {
        "video-transcoding": "SS",
        "video-od": "AR",
        "video-sr": "VC",
    }

    # Map scheduler directories to their names
    scheduler_mapping = {
        "default_all_tasks_dynamic": "default",
        "tutti_all_tasks_dynamic": "tutti",
        "smec_all_tasks_dynamic": "smec",
        "arma_all_tasks_dynamic": "arma",
    }

    # Dictionary to store all results
    all_data = {}

    # Process data for each application
    for app_dir, app_name in applications.items():
        slo_threshold = slo_thresholds[app_dir]
        print(f"\n=== Processing {app_name} (SLO: {slo_threshold}ms) ===")

        app_data = {}

        for scheduler_dir, scheduler_name in scheduler_mapping.items():
            # Process only client directory
            client_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "client"
            )

            if os.path.exists(client_path):
                print(f"  Processing {scheduler_name}/client...")
                _, total_frames, satisfied_frames = read_latency_data_with_slo(
                    client_path, slo_threshold, skip_lines=100, skip_tail=5
                )

                # Calculate satisfaction rate for this scheduler
                if total_frames > 0:
                    satisfaction_rate = (satisfied_frames / total_frames) * 100
                    app_data[scheduler_name] = satisfaction_rate
                    print(
                        f"  {scheduler_name}: {satisfaction_rate:.1f}%"
                        " satisfaction rate"
                        f" ({satisfied_frames}/{total_frames} frames)"
                    )
                else:
                    print(f"  {scheduler_name}: No valid data")
            else:
                print(f"  Client directory not found: {client_path}")

        if app_data:
            all_data[app_name] = app_data

    # Calculate geometric means for each scheduler
    schedulers = ["default", "tutti", "arma", "smec"]
    geomean_data = {}

    for scheduler in schedulers:
        values = []
        for app in applications.values():
            if app in all_data and scheduler in all_data[app]:
                values.append(all_data[app][scheduler])
        if values:
            # Calculate geometric mean
            geomean_data[scheduler] = np.power(
                np.prod(values), 1.0 / len(values)
            )

    # Create the bar chart
    plt.figure(figsize=(24, 7))

    # Set font properties
    plt.rcParams["font.family"] = ["DejaVu Sans", "Arial", "sans-serif"]
    plt.rcParams["font.weight"] = "normal"

    # Set style
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    # Define consistent colors and patterns for each scheduler type
    scheduler_styles = {
        "default": {"color": "#1f77b4", "label": "Default", "hatch": "/"},
        "tutti": {"color": "#9467bd", "label": "Tutti", "hatch": "-"},
        "smec": {"color": "#ff7f0e", "label": "SMEC", "hatch": None},
        "arma": {"color": "#2ca02c", "label": "ARMA", "hatch": "\\"},
    }

    # Prepare data for plotting
    app_names = list(applications.values())
    all_apps_with_geomean = app_names + ["Geomean"]

    # Calculate positions for grouped bars
    n_apps = len(all_apps_with_geomean)
    n_schedulers = len(schedulers)
    bar_width = 0.25
    bar_spacing = 0.02
    group_spacing = 0.8

    # Create x positions for each application group
    group_width = n_schedulers * (bar_width + bar_spacing) - bar_spacing
    app_positions = np.arange(n_apps) * (group_width + group_spacing)

    # Plot bars for each scheduler
    for i, scheduler in enumerate(schedulers):
        satisfaction_rates = []
        colors = []

        # Add data for original applications
        for app in app_names:
            if app in all_data and scheduler in all_data[app]:
                satisfaction_rates.append(all_data[app][scheduler])
            else:
                satisfaction_rates.append(0)  # Missing data

            colors.append(scheduler_styles[scheduler]["color"])

        # Add geometric mean data
        if scheduler in geomean_data:
            satisfaction_rates.append(geomean_data[scheduler])
        else:
            satisfaction_rates.append(0)
        colors.append(scheduler_styles[scheduler]["color"])

        # Calculate x positions for this scheduler across all applications
        x_positions = app_positions + i * (bar_width + bar_spacing)

        # Plot bars with patterns
        bars = plt.bar(
            x_positions,
            satisfaction_rates,
            width=bar_width,
            color=colors,
            alpha=0.9,
            hatch=scheduler_styles[scheduler]["hatch"],
            edgecolor="black",
            linewidth=1.2,
            label=scheduler_styles[scheduler]["label"],
        )

    # Customize the plot
    plt.ylabel(
        "SLO Satisfaction\nRate (%)",
        fontsize=52,
        fontweight="500",
        color="#2c3e50",
    )

    # Set x-axis labels at the center of each application group
    group_centers = app_positions + (group_width / 2)
    plt.xticks(
        group_centers, all_apps_with_geomean, fontsize=52, color="#2c3e50"
    )

    # Set y-axis limits and styling
    plt.ylim(0, 100)
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=52,
        colors="#2c3e50",
        width=1.5,
        length=8,
    )
    plt.tick_params(
        axis="x",
        which="major",
        labelsize=52,
        colors="#2c3e50",
        width=1.5,
        length=8,
    )

    # Enhanced grid
    plt.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, color="#bdc3c7")

    # Add legend
    plt.legend(
        fontsize=50,
        frameon=True,
        fancybox=True,
        shadow=True,
        bbox_to_anchor=(0.5, 0.98),
        loc="lower center",
        ncol=4,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
    )

    # Style enhancements
    plt.gca().spines["top"].set_linewidth(2.5)
    plt.gca().spines["top"].set_color("#333333")
    plt.gca().spines["right"].set_linewidth(2.5)
    plt.gca().spines["right"].set_color("#333333")
    plt.gca().spines["left"].set_linewidth(2.5)
    plt.gca().spines["left"].set_color("#333333")
    plt.gca().spines["bottom"].set_linewidth(2.5)
    plt.gca().spines["bottom"].set_color("#333333")

    # Set background color
    plt.gca().set_facecolor("#fafafa")

    plt.tight_layout()

    # Save the plot
    output_path = os.path.join(output_dir, "figure_13.pdf")
    plt.savefig(output_path, bbox_inches="tight", facecolor="white")

    print(f"\nFigure 13 saved as '{output_path}'")
    plt.close()


def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename for matching files"""
    match = re.search(r"(\d{8}_\d{9})", filename)
    if match:
        return match.group(1)
    return None


def calculate_network_latency_video_transcoding(
    client_dir, server_dir, skip_lines=100, skip_tail=5
):
    """
    Calculate network latency for video-transcoding (SS)

    Args:
        client_dir: Directory containing client latency files
        server_dir: Directory containing server process files
        skip_lines: Number of lines to skip from beginning
        skip_tail: Number of lines to skip from end

    Returns:
        list: Network latency values
    """
    # Get client files and sort by timestamp
    latency_files = glob.glob(os.path.join(client_dir, "latency_*.txt"))
    latency_files_with_ts = []
    for f in latency_files:
        ts = extract_timestamp_from_filename(f)
        if ts:
            latency_files_with_ts.append((ts, f))
    latency_files_with_ts.sort(key=lambda x: x[0])

    # Get server 2560 files and sort by timestamp
    process_files_2560 = glob.glob(
        os.path.join(server_dir, "process_2560*.txt")
    )
    process_files_with_ts = []
    for f in process_files_2560:
        ts = extract_timestamp_from_filename(f)
        if ts:
            process_files_with_ts.append((ts, f))
    process_files_with_ts.sort(key=lambda x: x[0])

    print(
        f"  Found {len(latency_files_with_ts)} client files and"
        f" {len(process_files_with_ts)} server 2560 files"
    )

    # Match by sorted order: smallest timestamp with smallest, largest with largest
    network_latencies = []
    num_pairs = min(len(latency_files_with_ts), len(process_files_with_ts))

    for i in range(num_pairs):
        latency_timestamp, latency_file = latency_files_with_ts[i]
        process_timestamp, matching_process_file = process_files_with_ts[i]

        print(
            f"    Matching: {os.path.basename(latency_file)} (ts:"
            f" {latency_timestamp}) <->"
            f" {os.path.basename(matching_process_file)} (ts:"
            f" {process_timestamp})"
        )

        # Read latency data with frame numbers
        latency_data_by_frame = {}
        try:
            df = pd.read_csv(latency_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 2:
                frame_column = df.iloc[:, 0]
                latency_column = df.iloc[:, 1]

                frames = []
                latencies = []
                for i in range(len(frame_column)):
                    try:
                        frame_num = int(frame_column.iloc[i])
                        e2e_latency = float(
                            str(latency_column.iloc[i])
                            .replace("ms", "")
                            .strip()
                        )
                        frames.append(frame_num)
                        latencies.append(e2e_latency)
                    except (ValueError, AttributeError):
                        continue

                # Skip head and tail
                if len(frames) > skip_lines + skip_tail:
                    frames = frames[skip_lines:-skip_tail]
                    latencies = latencies[skip_lines:-skip_tail]

                for frame_num, e2e_latency in zip(frames, latencies):
                    latency_data_by_frame[frame_num] = e2e_latency
        except Exception as e:
            print(f"    Error reading latency file: {e}")
            continue

        # Read process data with frame numbers (DO NOT skip any data from server)
        process_data_by_frame = {}
        try:
            df = pd.read_csv(matching_process_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 5:
                frame_column = df.iloc[:, 0]

                # SMEC has extra "Network Delay" column at the end
                # For SMEC: Total is at -2, for others: Total is at -1
                if "smec" in matching_process_file.lower():
                    total_column = df.iloc[:, -2]  # SMEC: second to last
                else:
                    total_column = df.iloc[
                        :, -1
                    ]  # Default/Tutti/ARMA: last column

                for i in range(len(frame_column)):
                    try:
                        frame_num = int(frame_column.iloc[i])
                        total_time = float(
                            str(total_column.iloc[i]).replace("ms", "").strip()
                        )
                        process_data_by_frame[frame_num] = total_time
                    except (ValueError, AttributeError):
                        continue

        except Exception as e:
            print(f"    Error reading process file: {e}")
            continue

        # Match by frame number and calculate network latency
        matched = 0
        for frame_num, e2e_latency in latency_data_by_frame.items():
            if frame_num in process_data_by_frame:
                total_time = process_data_by_frame[frame_num]
                network_latency = e2e_latency - total_time
                if network_latency > 0:
                    network_latencies.append(network_latency)
                    matched += 1

        print(f"    Generated {matched} network latency values")

    return network_latencies


def calculate_network_latency_ar_sr(
    client_dir, server_dir, skip_lines=100, skip_tail=5
):
    """
    Calculate network latency for AR/SR applications

    Args:
        client_dir: Directory containing client latency files
        server_dir: Directory containing server process files
        skip_lines: Number of lines to skip from beginning
        skip_tail: Number of lines to skip from end

    Returns:
        list: Network latency values
    """
    # Get client files and sort by timestamp
    latency_files = glob.glob(os.path.join(client_dir, "latency_*.txt"))
    latency_files_with_ts = []
    for f in latency_files:
        ts = extract_timestamp_from_filename(f)
        if ts:
            latency_files_with_ts.append((ts, f))
    latency_files_with_ts.sort(key=lambda x: x[0])

    print(f"  Found {len(latency_files_with_ts)} client files")

    # Map client file to stream ID: smaller timestamp -> stream 0, larger -> stream 1
    client_to_stream = {}
    if len(latency_files_with_ts) >= 2:
        client_to_stream[latency_files_with_ts[0][1]] = (
            0  # Smallest timestamp -> stream 0
        )
        client_to_stream[latency_files_with_ts[1][1]] = (
            1  # Largest timestamp -> stream 1
        )
        print(
            f"    {os.path.basename(latency_files_with_ts[0][1])} -> stream 0"
        )
        print(
            f"    {os.path.basename(latency_files_with_ts[1][1])} -> stream 1"
        )
    elif len(latency_files_with_ts) == 1:
        client_to_stream[latency_files_with_ts[0][1]] = 0
        print(
            f"    {os.path.basename(latency_files_with_ts[0][1])} -> stream 0"
        )

    # Read all process data organized by stream and frame (DO NOT skip any data from server)
    process_files = glob.glob(os.path.join(server_dir, "process_*.txt"))
    process_data_by_stream_frame = {}

    for process_file in process_files:
        print(f"    Reading process file: {os.path.basename(process_file)}")
        try:
            df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 6:
                stream_column = df.iloc[:, 0]
                frame_column = df.iloc[:, 1]

                # Determine Total column position based on scheduler and app type
                is_smec = "smec" in process_file.lower()
                is_ar = "yolo" in process_file

                if is_ar:
                    # AR: Default/Tutti/ARMA at -2, SMEC at -4
                    total_column = df.iloc[:, -4] if is_smec else df.iloc[:, -2]
                else:
                    # SR: Default/Tutti/ARMA at -1, SMEC at -3
                    total_column = df.iloc[:, -3] if is_smec else df.iloc[:, -1]

                # Group data by stream ID first
                stream_data = {}
                for i in range(len(stream_column)):
                    try:
                        stream_id = int(stream_column.iloc[i])
                        frame_num = int(frame_column.iloc[i])
                        total_time = float(
                            str(total_column.iloc[i]).replace("ms", "").strip()
                        )

                        if stream_id not in stream_data:
                            stream_data[stream_id] = []
                        stream_data[stream_id].append((frame_num, total_time))
                    except (ValueError, AttributeError):
                        continue

                # For each stream, skip first 100 and last 5 data points
                for stream_id, data_list in stream_data.items():
                    # Sort by frame number first
                    data_list.sort(key=lambda x: x[0])

                    if len(data_list) > skip_lines + skip_tail:
                        # Skip head and tail for this stream
                        filtered_data = data_list[skip_lines:-skip_tail]
                        for frame_num, total_time in filtered_data:
                            key = (stream_id, frame_num)
                            process_data_by_stream_frame[key] = total_time
                    else:
                        # If not enough data, include all
                        for frame_num, total_time in data_list:
                            key = (stream_id, frame_num)
                            process_data_by_stream_frame[key] = total_time

                print(
                    "    Extracted"
                    f" {len(process_data_by_stream_frame)} stream-frame pairs"
                    " (after filtering per stream)"
                )
        except Exception as e:
            print(f"    Error reading {process_file}: {e}")

    # Process each client latency file
    network_latencies = []
    for latency_file in client_to_stream.keys():
        stream_id = client_to_stream[latency_file]
        print(
            f"    Processing {os.path.basename(latency_file)} (stream"
            f" {stream_id})..."
        )

        # Read latency data
        try:
            df = pd.read_csv(latency_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 2:
                frame_column = df.iloc[:, 0]
                latency_column = df.iloc[:, 1]

                frames = []
                latencies = []
                for i in range(len(frame_column)):
                    try:
                        frame_num = int(frame_column.iloc[i])
                        e2e_latency = float(
                            str(latency_column.iloc[i])
                            .replace("ms", "")
                            .strip()
                        )
                        frames.append(frame_num)
                        latencies.append(e2e_latency)
                    except (ValueError, AttributeError):
                        continue

                # Skip head and tail
                if len(frames) > skip_lines + skip_tail:
                    frames = frames[skip_lines:-skip_tail]
                    latencies = latencies[skip_lines:-skip_tail]

                # Match with process data using the assigned stream ID
                matched = 0
                for frame_num, e2e_latency in zip(frames, latencies):
                    key = (stream_id, frame_num)
                    if key in process_data_by_stream_frame:
                        total_time = process_data_by_stream_frame[key]
                        network_latency = e2e_latency - total_time
                        if network_latency > 0:
                            network_latencies.append(network_latency)
                            matched += 1

                print(
                    f"      Generated {matched} network latency values from"
                    " this file"
                )
        except Exception as e:
            print(f"      Error reading latency file: {e}")

    return network_latencies


def generate_figure_15(results_base_path, output_dir):
    """
    Generate Figure 15: Network latency CDF across applications

    Args:
        results_base_path (str): Base path to results directory
        output_dir (str): Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define applications and their display names
    applications = {
        "video-transcoding": "SS",
        "video-od": "AR",
        "video-sr": "VC",
    }

    # Map scheduler directories to their names
    scheduler_mapping = {
        "default_all_tasks_dynamic": "default",
        "tutti_all_tasks_dynamic": "tutti",
        "smec_all_tasks_dynamic": "smec",
        "arma_all_tasks_dynamic": "arma",
    }

    # Store all data for plotting
    all_app_data = {}

    # Process each application
    for app_dir, app_name in applications.items():
        print(f"\n=== Processing {app_name} ({app_dir}) ===")
        all_app_data[app_name] = {}

        for scheduler_dir, scheduler_name in scheduler_mapping.items():
            client_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "client"
            )
            server_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "server"
            )

            if os.path.exists(client_path) and os.path.exists(server_path):
                print(f"  Processing {scheduler_name}...")

                # Calculate network latency based on app type
                if app_dir == "video-transcoding":
                    network_latencies = (
                        calculate_network_latency_video_transcoding(
                            client_path,
                            server_path,
                            skip_lines=100,
                            skip_tail=5,
                        )
                    )
                else:  # video-od or video-sr
                    network_latencies = calculate_network_latency_ar_sr(
                        client_path, server_path, skip_lines=100, skip_tail=5
                    )

                if network_latencies:
                    all_app_data[app_name][scheduler_name] = network_latencies
                    print(
                        f"    Total: {len(network_latencies)} network latency"
                        " values"
                    )
                    print(f"    Mean: {np.mean(network_latencies):.2f} ms")
                    print(f"    Median: {np.median(network_latencies):.2f} ms")
                    print(
                        "    95th percentile:"
                        f" {np.percentile(network_latencies, 95):.2f} ms"
                    )
                else:
                    print(f"    No network latency data found")
            else:
                if not os.path.exists(client_path):
                    print(f"  Client directory not found: {client_path}")
                if not os.path.exists(server_path):
                    print(f"  Server directory not found: {server_path}")

    # Create combined plot
    print(f"\n=== Creating combined network latency CDF plot ===")

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
        },
        "tutti": {
            "color": "#9467bd",
            "linestyle": ":",
            "marker": "v",
            "markevery": 400,
        },
        "smec": {
            "color": "#ff7f0e",
            "linestyle": "--",
            "marker": "s",
            "markevery": 400,
        },
        "arma": {
            "color": "#2ca02c",
            "linestyle": "-.",
            "marker": "^",
            "markevery": 400,
        },
    }

    # Legend labels
    legend_labels = {
        "default": "Default",
        "tutti": "Tutti",
        "smec": "SMEC",
        "arma": "ARMA",
    }

    # SLO values for network latency (same as E2E)
    slo_values = {"SS": 100, "AR": 100, "VC": 150}

    # Plot for each application
    for idx, app_name in enumerate(["SS", "AR", "VC"]):
        ax = axes[idx]

        if app_name in all_app_data:
            # Plot each scheduler for this application
            for scheduler in ["default", "tutti", "arma", "smec"]:
                if scheduler in all_app_data[app_name]:
                    network_latencies = all_app_data[app_name][scheduler]
                    sorted_data, cdf_values = calculate_cdf(network_latencies)

                    ax.plot(
                        sorted_data,
                        cdf_values,
                        color=plot_configs[scheduler]["color"],
                        linestyle=plot_configs[scheduler]["linestyle"],
                        linewidth=6,
                        label=legend_labels[scheduler],
                        alpha=0.9,
                        marker=plot_configs[scheduler]["marker"],
                        markevery=plot_configs[scheduler]["markevery"],
                        markersize=12,
                        markerfacecolor="white",
                        markeredgewidth=3,
                        markeredgecolor=plot_configs[scheduler]["color"],
                    )

            # Add SLO line
            if app_name in slo_values:
                ax.axvline(
                    x=slo_values[app_name],
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
        ax.set_xlim(left=10)

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
        ax.xaxis.set_major_locator(ticker.FixedLocator([100, 1000, 10000]))

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
    output_path = os.path.join(output_dir, "figure_15.pdf")
    plt.savefig(output_path, bbox_inches="tight")

    print(f"\nFigure 15 saved as '{output_path}'")
    plt.close()


def read_processing_time_data(
    client_dir, server_dir, app_type, skip_lines=100, skip_tail=5
):
    """
    Read processing time data by matching client and server data
    Only keep processing times where processing_time < e2e_latency

    Args:
        client_dir: Directory containing client latency files
        server_dir: Directory containing server process files
        app_type: Application type ('video-transcoding', 'video-od', 'video-sr')
        skip_lines: Number of lines to skip from beginning (applied to client data)
        skip_tail: Number of lines to skip from end (applied to client data)

    Returns:
        list: Processing time values (filtered)
    """
    all_processing_times = []

    if app_type == "video-transcoding":
        # Use existing SS matching logic from Figure 15
        # Get client files and sort by timestamp
        latency_files = glob.glob(os.path.join(client_dir, "latency_*.txt"))
        latency_files_with_ts = []
        for f in latency_files:
            ts = extract_timestamp_from_filename(f)
            if ts:
                latency_files_with_ts.append((ts, f))
        latency_files_with_ts.sort(key=lambda x: x[0])

        # Get server 2560 files and sort by timestamp
        process_files_2560 = glob.glob(
            os.path.join(server_dir, "process_2560*.txt")
        )
        process_files_with_ts = []
        for f in process_files_2560:
            ts = extract_timestamp_from_filename(f)
            if ts:
                process_files_with_ts.append((ts, f))
        process_files_with_ts.sort(key=lambda x: x[0])

        num_pairs = min(len(latency_files_with_ts), len(process_files_with_ts))

        for i in range(num_pairs):
            _, latency_file = latency_files_with_ts[i]
            _, process_file = process_files_with_ts[i]

            # Read client E2E latency data (skip head and tail)
            client_data_by_frame = {}
            try:
                df = pd.read_csv(latency_file, sep=r"\s+", skiprows=1)
                if len(df.columns) >= 2:
                    frame_column = df.iloc[:, 0]
                    latency_column = df.iloc[:, 1]

                    frames = []
                    latencies = []
                    for j in range(len(frame_column)):
                        try:
                            frame_num = int(frame_column.iloc[j])
                            e2e_latency = float(
                                str(latency_column.iloc[j])
                                .replace("ms", "")
                                .strip()
                            )
                            frames.append(frame_num)
                            latencies.append(e2e_latency)
                        except (ValueError, AttributeError):
                            continue

                    # Skip head and tail
                    if len(frames) > skip_lines + skip_tail:
                        frames = frames[skip_lines:-skip_tail]
                        latencies = latencies[skip_lines:-skip_tail]

                    for frame_num, e2e_latency in zip(frames, latencies):
                        client_data_by_frame[frame_num] = e2e_latency
            except Exception as e:
                print(f"    Error reading client file: {e}")
                continue

            # Read server processing time data
            server_data_by_frame = {}
            try:
                df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
                if len(df.columns) >= 5:
                    frame_column = df.iloc[:, 0]
                    is_smec = "smec" in process_file.lower()
                    total_column = df.iloc[:, -2] if is_smec else df.iloc[:, -1]

                    # For SMEC, last column is estimated network latency
                    estimated_network_column = (
                        df.iloc[:, -1] if is_smec else None
                    )

                    for j in range(len(frame_column)):
                        try:
                            frame_num = int(frame_column.iloc[j])
                            total_time = float(
                                str(total_column.iloc[j])
                                .replace("ms", "")
                                .strip()
                            )

                            # For SMEC, also read estimated network latency
                            estimated_network = None
                            if is_smec and estimated_network_column is not None:
                                estimated_network = float(
                                    str(estimated_network_column.iloc[j])
                                    .replace("ms", "")
                                    .strip()
                                )

                            server_data_by_frame[frame_num] = (
                                total_time,
                                estimated_network,
                            )
                        except (ValueError, AttributeError):
                            continue
            except Exception as e:
                print(f"    Error reading server file: {e}")
                continue

            # Match and filter: only keep processing_time < e2e_latency and processing_time > 0
            # For SMEC, also filter estimated_network_latency > 0
            for frame_num, e2e_latency in client_data_by_frame.items():
                if frame_num in server_data_by_frame:
                    processing_time, estimated_network = server_data_by_frame[
                        frame_num
                    ]

                    # Check processing time is valid
                    if processing_time > 0 and processing_time < e2e_latency:
                        # For SMEC, also check estimated network latency
                        if estimated_network is not None:
                            if estimated_network > 0:
                                all_processing_times.append(processing_time)
                        else:
                            # Not SMEC, no estimated network check needed
                            all_processing_times.append(processing_time)

    else:  # video-od or video-sr
        # Use existing AR/SR matching logic from Figure 15
        # Get client files and sort by timestamp
        latency_files = glob.glob(os.path.join(client_dir, "latency_*.txt"))
        latency_files_with_ts = []
        for f in latency_files:
            ts = extract_timestamp_from_filename(f)
            if ts:
                latency_files_with_ts.append((ts, f))
        latency_files_with_ts.sort(key=lambda x: x[0])

        # Map client file to stream ID
        client_to_stream = {}
        if len(latency_files_with_ts) >= 2:
            client_to_stream[latency_files_with_ts[0][1]] = 0
            client_to_stream[latency_files_with_ts[1][1]] = 1
        elif len(latency_files_with_ts) == 1:
            client_to_stream[latency_files_with_ts[0][1]] = 0

        # Read all server process data
        process_files = glob.glob(os.path.join(server_dir, "process_*.txt"))
        server_data_by_stream_frame = {}

        for process_file in process_files:
            try:
                df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
                if len(df.columns) >= 6:
                    stream_column = df.iloc[:, 0]
                    frame_column = df.iloc[:, 1]

                    is_smec = "smec" in process_file.lower()
                    is_ar = "yolo" in process_file

                    if is_ar:
                        total_column = (
                            df.iloc[:, -4] if is_smec else df.iloc[:, -2]
                        )
                    else:
                        total_column = (
                            df.iloc[:, -3] if is_smec else df.iloc[:, -1]
                        )

                    # For SMEC, last column is estimated network latency
                    estimated_network_column = (
                        df.iloc[:, -1] if is_smec else None
                    )

                    for j in range(len(stream_column)):
                        try:
                            stream_id = int(stream_column.iloc[j])
                            frame_num = int(frame_column.iloc[j])
                            total_time = float(
                                str(total_column.iloc[j])
                                .replace("ms", "")
                                .strip()
                            )

                            # For SMEC, also read estimated network latency
                            estimated_network = None
                            if is_smec and estimated_network_column is not None:
                                estimated_network = float(
                                    str(estimated_network_column.iloc[j])
                                    .replace("ms", "")
                                    .strip()
                                )

                            key = (stream_id, frame_num)
                            server_data_by_stream_frame[key] = (
                                total_time,
                                estimated_network,
                            )
                        except (ValueError, AttributeError):
                            continue
            except Exception as e:
                print(f"    Error reading {process_file}: {e}")

        # Process each client file
        for latency_file in client_to_stream.keys():
            stream_id = client_to_stream[latency_file]

            try:
                df = pd.read_csv(latency_file, sep=r"\s+", skiprows=1)
                if len(df.columns) >= 2:
                    frame_column = df.iloc[:, 0]
                    latency_column = df.iloc[:, 1]

                    frames = []
                    latencies = []
                    for j in range(len(frame_column)):
                        try:
                            frame_num = int(frame_column.iloc[j])
                            e2e_latency = float(
                                str(latency_column.iloc[j])
                                .replace("ms", "")
                                .strip()
                            )
                            frames.append(frame_num)
                            latencies.append(e2e_latency)
                        except (ValueError, AttributeError):
                            continue

                    # Skip head and tail
                    if len(frames) > skip_lines + skip_tail:
                        frames = frames[skip_lines:-skip_tail]
                        latencies = latencies[skip_lines:-skip_tail]

                    # Match with server data and filter
                    for frame_num, e2e_latency in zip(frames, latencies):
                        key = (stream_id, frame_num)
                        if key in server_data_by_stream_frame:
                            processing_time, estimated_network = (
                                server_data_by_stream_frame[key]
                            )

                            # Check processing time is valid
                            if (
                                processing_time > 0
                                and processing_time < e2e_latency
                            ):
                                # For SMEC, also check estimated network latency
                                if estimated_network is not None:
                                    if estimated_network > 0:
                                        all_processing_times.append(
                                            processing_time
                                        )
                                else:
                                    # Not SMEC, no estimated network check needed
                                    all_processing_times.append(processing_time)
            except Exception as e:
                print(f"    Error reading latency file: {e}")

    return all_processing_times


def generate_figure_16(results_base_path, output_dir):
    """
    Generate Figure 16: Processing time CDF across applications

    Args:
        results_base_path (str): Base path to results directory
        output_dir (str): Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define applications and their display names
    applications = {
        "video-transcoding": "SS",
        "video-od": "AR",
        "video-sr": "VC",
    }

    # Map scheduler directories to their names
    scheduler_mapping = {
        "default_all_tasks_dynamic": "default",
        "tutti_all_tasks_dynamic": "tutti",
        "smec_all_tasks_dynamic": "smec",
        "arma_all_tasks_dynamic": "arma",
    }

    # Store all data for plotting
    all_app_data = {}

    # Process each application
    for app_dir, app_name in applications.items():
        print(f"\n=== Processing {app_name} ({app_dir}) ===")
        all_app_data[app_name] = {}

        for scheduler_dir, scheduler_name in scheduler_mapping.items():
            client_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "client"
            )
            server_path = os.path.join(
                results_base_path, scheduler_dir, app_dir, "server"
            )

            if os.path.exists(client_path) and os.path.exists(server_path):
                print(f"  Processing {scheduler_name}...")

                processing_times = read_processing_time_data(
                    client_path,
                    server_path,
                    app_dir,
                    skip_lines=100,
                    skip_tail=5,
                )

                if processing_times:
                    all_app_data[app_name][scheduler_name] = processing_times
                    print(
                        f"    Total: {len(processing_times)} processing time"
                        " values"
                    )
                    print(f"    Mean: {np.mean(processing_times):.2f} ms")
                    print(f"    Median: {np.median(processing_times):.2f} ms")
                    print(
                        "    95th percentile:"
                        f" {np.percentile(processing_times, 95):.2f} ms"
                    )
                else:
                    print(f"    No processing time data found")
            else:
                if not os.path.exists(client_path):
                    print(f"  Client directory not found: {client_path}")
                if not os.path.exists(server_path):
                    print(f"  Server directory not found: {server_path}")

    # Create combined plot
    print(f"\n=== Creating combined processing time CDF plot ===")

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
            "markevery": 200,
        },
        "tutti": {
            "color": "#9467bd",
            "linestyle": ":",
            "marker": "v",
            "markevery": 200,
        },
        "smec": {
            "color": "#ff7f0e",
            "linestyle": "--",
            "marker": "s",
            "markevery": 200,
        },
        "arma": {
            "color": "#2ca02c",
            "linestyle": "-.",
            "marker": "^",
            "markevery": 200,
        },
    }

    # Legend labels
    legend_labels = {
        "default": "Default",
        "tutti": "Tutti",
        "smec": "SMEC",
        "arma": "ARMA",
    }

    # SLO values for processing time (same as E2E)
    slo_values = {"SS": 100, "AR": 100, "VC": 150}

    # Plot for each application
    for idx, app_name in enumerate(["SS", "AR", "VC"]):
        ax = axes[idx]

        if app_name in all_app_data:
            # Plot each scheduler for this application
            for scheduler in ["default", "tutti", "arma", "smec"]:
                if scheduler in all_app_data[app_name]:
                    processing_times = all_app_data[app_name][scheduler]
                    sorted_data, cdf_values = calculate_cdf(processing_times)

                    ax.plot(
                        sorted_data,
                        cdf_values,
                        color=plot_configs[scheduler]["color"],
                        linestyle=plot_configs[scheduler]["linestyle"],
                        linewidth=6,
                        label=legend_labels[scheduler],
                        alpha=0.9,
                        marker=plot_configs[scheduler]["marker"],
                        markevery=plot_configs[scheduler]["markevery"],
                        markersize=12,
                        markerfacecolor="white",
                        markeredgewidth=3,
                        markeredgecolor=plot_configs[scheduler]["color"],
                    )

            # Add SLO line
            if app_name in slo_values:
                ax.axvline(
                    x=slo_values[app_name],
                    color="#d62728",
                    linestyle=":",
                    linewidth=8,
                    alpha=0.8,
                    zorder=5,
                )

        # Customize each subplot
        ax.set_xlabel(f"{app_name}", fontsize=52, color="#333333")

        # Set axis properties - LINEAR scale (not log)
        ax.set_ylim(0, 1.05)
        ax.set_xlim(left=0)

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
        ax.xaxis.set_major_locator(
            ticker.MultipleLocator(100)
        )  # 100ms intervals

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
    output_path = os.path.join(output_dir, "figure_16.pdf")
    plt.savefig(output_path, bbox_inches="tight")

    print(f"\nFigure 16 saved as '{output_path}'")
    plt.close()
