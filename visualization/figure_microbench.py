import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import re


def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename for matching files"""
    match = re.search(r"(\d{8}_\d{9})", filename)
    if match:
        return match.group(1)
    return None


def collect_processing_time_for_method_app(
    method_dir, app_name, skip_lines=100, skip_tail=5
):
    """
    Collect processing time data for a specific method and app
    Only keep processing times where processing_time < e2e_latency

    Args:
        method_dir: Directory path for the method (e.g., smec_all_tasks)
        app_name: Application name (video-transcoding, video-od, video-sr)
        skip_lines: Number of lines to skip from beginning (applied to client data)
        skip_tail: Number of lines to skip from end (applied to client data)

    Returns:
        list: All processing time values (filtered)
    """
    client_dir = os.path.join(method_dir, app_name, "client")
    server_dir = os.path.join(method_dir, app_name, "server")

    if not os.path.exists(client_dir):
        print(f"Client directory not found: {client_dir}")
        return []

    if not os.path.exists(server_dir):
        print(f"Server directory not found: {server_dir}")
        return []

    all_processing_times = []
    is_smec = (
        "smec_all_tasks" in method_dir
        and "disable" not in method_dir
        and "rtt" not in method_dir
    )

    if app_name == "video-transcoding":
        # Get client files and sort by timestamp
        latency_files = glob.glob(os.path.join(client_dir, "latency_*.txt"))
        latency_files_with_ts = []
        for f in latency_files:
            ts = extract_timestamp_from_filename(f)
            if ts:
                latency_files_with_ts.append((ts, f))
        latency_files_with_ts.sort(key=lambda x: x[0])

        # Get server 2560x1440 files and sort by timestamp
        process_files_2560 = glob.glob(
            os.path.join(server_dir, "process_2560x1440_*.txt")
        )
        process_files_with_ts = []
        for f in process_files_2560:
            ts = extract_timestamp_from_filename(f)
            if ts:
                process_files_with_ts.append((ts, f))
        process_files_with_ts.sort(key=lambda x: x[0])

        num_pairs = min(len(latency_files_with_ts), len(process_files_with_ts))
        print(f"  Found {num_pairs} matching client-server file pairs")

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
                    # Transcoding: Total always at -2 (all methods have Network Delay column)
                    total_column = df.iloc[:, -2]

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
            matched = 0
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
                                matched += 1
                        else:
                            # Not SMEC, no estimated network check needed
                            all_processing_times.append(processing_time)
                            matched += 1

            print(
                f"    Matched {matched} valid data points from"
                f" {os.path.basename(latency_file)}"
            )

    else:  # video-od or video-sr
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
        if app_name == "video-od":
            process_files = glob.glob(
                os.path.join(server_dir, "process_yolo_*.txt")
            )
        else:  # video-sr
            process_files = glob.glob(
                os.path.join(server_dir, "process_sr_*.txt")
            )

        server_data_by_stream_frame = {}

        for process_file in process_files:
            print(f"  Reading server file: {os.path.basename(process_file)}")
            try:
                df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
                if len(df.columns) >= 6:
                    stream_column = df.iloc[:, 0]
                    frame_column = df.iloc[:, 1]

                    # Determine Total column position
                    is_ar = "yolo" in process_file
                    if is_ar:
                        # AR: Total always at -4 (column 5, all methods have same format)
                        total_column = df.iloc[:, -4]
                    else:
                        # SR: Total always at -3 (column 5, all methods have same format)
                        total_column = df.iloc[:, -3]

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
            print(
                f"  Processing {os.path.basename(latency_file)} (stream"
                f" {stream_id})..."
            )

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
                    matched = 0
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
                                        matched += 1
                                else:
                                    # Not SMEC, no estimated network check needed
                                    all_processing_times.append(processing_time)
                                    matched += 1

                    print(f"    Matched {matched} valid data points")
            except Exception as e:
                print(f"    Error reading latency file: {e}")

    print(
        f"  Total valid data points for {app_name}: {len(all_processing_times)}"
    )
    return all_processing_times


def calculate_cdf(data):
    """Calculate CDF for the given data"""
    if not data:
        return [], []

    sorted_data = np.sort(data)
    n = len(sorted_data)
    cdf_values = np.arange(1, n + 1) / n

    return sorted_data, cdf_values


def generate_figure_18_a(results_base_path, output_dir):
    """
    Generate Figure 18-a: Processing time CDF for Default, PARTIES, and SMEC

    Args:
        results_base_path: Base path to results directory
        output_dir: Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define methods and their directory names
    method_dirs = {
        "default": os.path.join(results_base_path, "smec_all_tasks_disable"),
        "parties": os.path.join(results_base_path, "smec_all_tasks_rtt"),
        "smec": os.path.join(results_base_path, "smec_all_tasks"),
    }

    # Define applications
    apps = ["video-transcoding", "video-od", "video-sr"]

    # Color and style configuration
    plot_configs = {
        "smec": {
            "color": "#ff7f0e",
            "linestyle": "--",
            "marker": "s",
            "markevery": 200,
        },  # orange dashed
        "parties": {
            "color": "#9467bd",
            "linestyle": ":",
            "marker": "v",
            "markevery": 200,
        },  # purple dotted
        "default": {
            "color": "#1f77b4",
            "linestyle": "-",
            "marker": "o",
            "markevery": 200,
        },  # blue solid
    }

    legend_labels = {"smec": "SMEC", "parties": "PARTIES", "default": "Default"}

    app_titles = {"video-od": "AR", "video-sr": "VC", "video-transcoding": "SS"}

    # Store data for all apps
    all_app_data = {}

    # Process each app
    for app_name in apps:
        print(f"\n=== Processing {app_name} ===")
        all_app_data[app_name] = {}

        # Process each method for this app
        for method_key, method_dir in method_dirs.items():
            if os.path.exists(method_dir):
                print(f"  Processing method: {method_key}")
                processing_times = collect_processing_time_for_method_app(
                    method_dir, app_name
                )

                if processing_times:
                    all_app_data[app_name][method_key] = processing_times

                    # Print statistics
                    print(f"    Statistics for {method_key}:")
                    print(f"      - Mean: {np.mean(processing_times):.2f} ms")
                    print(
                        f"      - Median: {np.median(processing_times):.2f} ms"
                    )
                    print(
                        "      - 95th percentile:"
                        f" {np.percentile(processing_times, 95):.2f} ms"
                    )
                    print(
                        "      - 99th percentile:"
                        f" {np.percentile(processing_times, 99):.2f} ms"
                    )
                else:
                    print(f"    No data found for {method_key}")
            else:
                print(f"  Method directory not found: {method_dir}")

    # Create combined plot with all three apps as subplots
    print(f"\n=== Creating Figure 18-a plot ===")

    fig, axes = plt.subplots(1, 3, figsize=(21, 6.5), sharey=True)

    # Try to use seaborn style
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    for app_idx, app_name in enumerate(apps):
        ax = axes[app_idx]

        # Plot each method for this app
        for method in ["default", "parties", "smec"]:
            if (
                method in all_app_data[app_name]
                and all_app_data[app_name][method]
            ):
                processing_times = all_app_data[app_name][method]
                sorted_data, cdf_values = calculate_cdf(processing_times)

                ax.plot(
                    sorted_data,
                    cdf_values,
                    color=plot_configs[method]["color"],
                    linestyle=plot_configs[method]["linestyle"],
                    linewidth=6,
                    label=legend_labels[method],
                    alpha=0.9,
                    marker=plot_configs[method]["marker"],
                    markevery=plot_configs[method]["markevery"],
                    markersize=12,
                    markerfacecolor="white",
                    markeredgewidth=3,
                    markeredgecolor=plot_configs[method]["color"],
                )

        # Customize subplot
        ax.set_xlabel(f"{app_titles[app_name]}", fontsize=52, color="#333333")

        # Set axis properties
        ax.set_ylim(0, 1.05)
        ax.set_xlim(left=0)

        # Enhanced grid and styling
        ax.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")
        ax.set_facecolor("#fafafa")

        # Enhanced ticks
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=52,
            colors="#333333",
            width=2,
            length=8,
        )

        # Enhanced spines
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
            spine.set_color("#333333")

        # Add SLO vertical lines
        slo_values = {
            "video-od": 100,
            "video-sr": 150,
            "video-transcoding": 100,
        }
        if app_name in slo_values:
            ax.axvline(
                x=slo_values[app_name],
                color="#d62728",
                linestyle=":",
                linewidth=8,
                alpha=0.8,
                zorder=5,
            )

        # Set custom ticks
        import matplotlib.ticker as ticker

        ax.yaxis.set_major_locator(ticker.FixedLocator([0, 0.5, 1.0]))

        # Set x-axis ticks
        if app_name == "video-sr":
            ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
        else:
            ax.xaxis.set_major_locator(ticker.MultipleLocator(100))

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
        ncol=4,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
        columnspacing=0.8,
        handletextpad=0.3,
    )

    # Adjust layout
    plt.tight_layout()

    # Save plot (PDF only)
    output_path_pdf = os.path.join(output_dir, "figure_18_a.pdf")
    plt.savefig(
        output_path_pdf, dpi=300, bbox_inches="tight", facecolor="white"
    )

    print(f"\nFigure 18-a saved as: {output_path_pdf}")

    # Close the figure
    plt.close()


def generate_figure_18_b(results_base_path, output_dir):
    """
    Generate Figure 18-b: Processing time CDF for Default, PARTIES, and SMEC (Dynamic Workload)

    Args:
        results_base_path: Base path to results directory
        output_dir: Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define methods and their directory names (dynamic workload)
    method_dirs = {
        "default": os.path.join(
            results_base_path, "smec_all_tasks_dynamic_disable"
        ),
        "parties": os.path.join(
            results_base_path, "smec_all_tasks_dynamic_rtt"
        ),
        "smec": os.path.join(results_base_path, "smec_all_tasks_dynamic"),
    }

    # Define applications
    apps = ["video-transcoding", "video-od", "video-sr"]

    # Color and style configuration
    plot_configs = {
        "smec": {
            "color": "#ff7f0e",
            "linestyle": "--",
            "marker": "s",
            "markevery": 200,
        },  # orange dashed
        "parties": {
            "color": "#9467bd",
            "linestyle": ":",
            "marker": "v",
            "markevery": 200,
        },  # purple dotted
        "default": {
            "color": "#1f77b4",
            "linestyle": "-",
            "marker": "o",
            "markevery": 200,
        },  # blue solid
    }

    legend_labels = {"smec": "SMEC", "parties": "PARTIES", "default": "Default"}

    app_titles = {"video-od": "AR", "video-sr": "VC", "video-transcoding": "SS"}

    # Store data for all apps
    all_app_data = {}

    # Process each app
    for app_name in apps:
        print(f"\n=== Processing {app_name} ===")
        all_app_data[app_name] = {}

        # Process each method for this app
        for method_key, method_dir in method_dirs.items():
            if os.path.exists(method_dir):
                print(f"  Processing method: {method_key}")
                processing_times = collect_processing_time_for_method_app(
                    method_dir, app_name
                )

                if processing_times:
                    all_app_data[app_name][method_key] = processing_times

                    # Print statistics
                    print(f"    Statistics for {method_key}:")
                    print(f"      - Mean: {np.mean(processing_times):.2f} ms")
                    print(
                        f"      - Median: {np.median(processing_times):.2f} ms"
                    )
                    print(
                        "      - 95th percentile:"
                        f" {np.percentile(processing_times, 95):.2f} ms"
                    )
                    print(
                        "      - 99th percentile:"
                        f" {np.percentile(processing_times, 99):.2f} ms"
                    )
                else:
                    print(f"    No data found for {method_key}")
            else:
                print(f"  Method directory not found: {method_dir}")

    # Create combined plot with all three apps as subplots
    print(f"\n=== Creating Figure 18-b plot ===")

    fig, axes = plt.subplots(1, 3, figsize=(21, 6.5), sharey=True)

    # Try to use seaborn style
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    for app_idx, app_name in enumerate(apps):
        ax = axes[app_idx]

        # Plot each method for this app
        for method in ["default", "parties", "smec"]:
            if (
                method in all_app_data[app_name]
                and all_app_data[app_name][method]
            ):
                processing_times = all_app_data[app_name][method]
                sorted_data, cdf_values = calculate_cdf(processing_times)

                ax.plot(
                    sorted_data,
                    cdf_values,
                    color=plot_configs[method]["color"],
                    linestyle=plot_configs[method]["linestyle"],
                    linewidth=6,
                    label=legend_labels[method],
                    alpha=0.9,
                    marker=plot_configs[method]["marker"],
                    markevery=plot_configs[method]["markevery"],
                    markersize=12,
                    markerfacecolor="white",
                    markeredgewidth=3,
                    markeredgecolor=plot_configs[method]["color"],
                )

        # Customize subplot
        ax.set_xlabel(f"{app_titles[app_name]}", fontsize=52, color="#333333")

        # Set axis properties
        ax.set_ylim(0, 1.05)
        ax.set_xlim(left=0)

        # Enhanced grid and styling
        ax.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")
        ax.set_facecolor("#fafafa")

        # Enhanced ticks
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=52,
            colors="#333333",
            width=2,
            length=8,
        )

        # Enhanced spines
        for spine in ax.spines.values():
            spine.set_linewidth(2.5)
            spine.set_color("#333333")

        # Add SLO vertical lines
        slo_values = {
            "video-od": 100,
            "video-sr": 150,
            "video-transcoding": 100,
        }
        if app_name in slo_values:
            ax.axvline(
                x=slo_values[app_name],
                color="#d62728",
                linestyle=":",
                linewidth=8,
                alpha=0.8,
                zorder=5,
            )

        # Set custom ticks
        import matplotlib.ticker as ticker

        ax.yaxis.set_major_locator(ticker.FixedLocator([0, 0.5, 1.0]))

        # Set x-axis ticks
        if app_name == "video-sr":
            ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
        else:
            ax.xaxis.set_major_locator(ticker.MultipleLocator(100))

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
        ncol=4,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
        columnspacing=0.8,
        handletextpad=0.3,
    )

    # Adjust layout
    plt.tight_layout()

    # Save plot (PDF only)
    output_path_pdf = os.path.join(output_dir, "figure_18_b.pdf")
    plt.savefig(
        output_path_pdf, dpi=300, bbox_inches="tight", facecolor="white"
    )

    print(f"\nFigure 18-b saved as: {output_path_pdf}")

    # Close the figure
    plt.close()


def read_latency_data_with_filtering(
    directory_path, slo_threshold, skip_head=100, skip_tail=5
):
    """
    Read E2E latency data from client directory with filtering

    Args:
        directory_path: Path to client directory containing latency files
        slo_threshold: SLO threshold in milliseconds
        skip_head: Number of lines to skip from the beginning
        skip_tail: Number of lines to skip from the end

    Returns:
        tuple: (all_latencies, total_frames, satisfied_frames)
    """
    all_latencies = []
    total_frames = 0
    satisfied_frames = 0

    # Find all latency files
    file_pattern = os.path.join(directory_path, "latency_*.txt")
    files = glob.glob(file_pattern)

    print(f"  Processing {len(files)} files...")

    for file_path in files:
        try:
            # Read the file, skip header
            df = pd.read_csv(file_path, sep=r"\s+", skiprows=1)

            if len(df.columns) >= 2:
                frame_column = df.iloc[:, 0]
                latency_column = df.iloc[:, 1]

                # Convert to lists
                frames = []
                latencies = []

                for i in range(len(frame_column)):
                    try:
                        frame_num = int(frame_column.iloc[i])
                        latency_val = float(
                            str(latency_column.iloc[i])
                            .replace("ms", "")
                            .strip()
                        )
                        frames.append(frame_num)
                        latencies.append(latency_val)
                    except (ValueError, AttributeError):
                        continue

                # Filter: skip head and tail
                if len(frames) > skip_head + skip_tail:
                    frames = frames[skip_head:-skip_tail]
                    latencies = latencies[skip_head:-skip_tail]

                if len(frames) > 0:
                    # Calculate total frames based on frame indices
                    min_frame = min(frames)
                    max_frame = max(frames)
                    file_total_frames = max_frame - min_frame + 1
                    file_satisfied_frames = sum(
                        1 for lat in latencies if lat <= slo_threshold
                    )

                    all_latencies.extend(latencies)
                    total_frames += file_total_frames
                    satisfied_frames += file_satisfied_frames

                    print(
                        f"    {os.path.basename(file_path)}:"
                        f" {file_total_frames} frames,"
                        f" {file_satisfied_frames}/{len(latencies)} satisfied"
                    )

        except Exception as e:
            print(f"    Error reading {file_path}: {e}")

    return all_latencies, total_frames, satisfied_frames


def collect_drop_performance_data(results_base_path):
    """
    Collect SLO satisfaction data for drop performance comparison

    Args:
        results_base_path: Base path to results directory

    Returns:
        dict: Dictionary containing data organized by workload, condition, and app
    """
    # Define applications and their SLO thresholds
    applications = {
        "video-transcoding": {"name": "SS", "slo": 100.0},
        "video-od": {"name": "AR", "slo": 100.0},
        "video-sr": {"name": "VC", "slo": 150.0},
    }

    # Define directory mappings
    directory_mapping = {
        "static": {
            "drop": "smec_all_tasks",
            "wo-drop": "smec_all_tasks_wo_drop",
        },
        "dynamic": {
            "drop": "smec_all_tasks_dynamic",
            "wo-drop": "smec_all_tasks_dynamic_wo_drop",
        },
    }

    # Dictionary to store all results
    all_data = {}

    for workload_type in ["static", "dynamic"]:
        workload_data = {}
        print(f"\n=== Processing {workload_type} workload ===")

        for condition in ["drop", "wo-drop"]:
            condition_data = {}
            dir_name = directory_mapping[workload_type][condition]
            method_dir = os.path.join(results_base_path, dir_name)

            print(f"  Condition: {condition} ({dir_name})")

            if not os.path.exists(method_dir):
                print(f"    Directory not found: {method_dir}")
                continue

            for app_key, app_info in applications.items():
                app_name = app_info["name"]
                slo_threshold = app_info["slo"]

                # Client directory path
                client_dir = os.path.join(method_dir, app_key, "client")

                if os.path.exists(client_dir):
                    print(f"    Processing {app_name} (SLO: {slo_threshold}ms)")
                    _, total_frames, satisfied_frames = (
                        read_latency_data_with_filtering(
                            client_dir,
                            slo_threshold,
                            skip_head=100,
                            skip_tail=5,
                        )
                    )

                    if total_frames > 0:
                        satisfaction_rate = (
                            satisfied_frames / total_frames
                        ) * 100
                        condition_data[app_name] = satisfaction_rate
                        print(
                            f"      Satisfaction rate: {satisfaction_rate:.1f}%"
                        )
                    else:
                        condition_data[app_name] = 0
                        print(f"      No valid data")
                else:
                    condition_data[app_name] = 0
                    print(f"    {app_name}: Client directory not found")

            workload_data[condition] = condition_data

        all_data[workload_type] = workload_data

    return all_data


def generate_figure_21(results_base_path, output_dir):
    """
    Generate Figure 21: Drop Performance Comparison

    Args:
        results_base_path: Base path to results directory
        output_dir: Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print("=== Drop Performance Analysis (Figure 21) ===")

    # Collect data
    all_data = collect_drop_performance_data(results_base_path)

    if not all_data:
        print("No data found for any workloads")
        return

    # Print summary
    print("\n=== SUMMARY ===")
    for workload, workload_data in all_data.items():
        print(f"{workload}:")
        for condition, condition_data in workload_data.items():
            print(f"  {condition}:")
            for app_name, satisfaction_rate in condition_data.items():
                print(f"    {app_name}: {satisfaction_rate:.1f}%")

    # Create bar chart
    print("\n=== Creating Figure 21 ===")

    plt.figure(figsize=(17, 5.5))

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

    # Define colors for applications
    app_colors = {
        "SS": "#2ca02c",  # green
        "AR": "#1f77b4",  # blue
        "VC": "#ff7f0e",  # orange
    }

    # Prepare data for plotting
    applications = ["SS", "AR", "VC"]
    workloads = ["static", "dynamic"]
    conditions = ["drop", "wo-drop"]

    # Calculate positions for grouped bars
    n_workloads = len(workloads)
    n_conditions = len(conditions)
    n_apps = len(applications)

    # Bar width and spacing
    bar_width = 0.18
    app_spacing = 0.04
    condition_group_width = n_apps * bar_width + (n_apps - 1) * app_spacing
    condition_spacing = 0.4
    workload_spacing = 0.8

    # Create positions for workload groups
    workload_base_positions = np.arange(n_workloads) * (
        n_conditions * condition_group_width
        + condition_spacing
        + workload_spacing
    )

    # Plot bars
    for workload_idx, workload in enumerate(workloads):
        workload_base = workload_base_positions[workload_idx]

        for cond_idx, condition in enumerate(conditions):
            # Calculate base position for this condition group
            condition_base = workload_base + cond_idx * (
                condition_group_width + condition_spacing
            )

            for app_idx, app in enumerate(applications):
                # Get the satisfaction rate for this combination
                satisfaction_rate = 0
                if (
                    workload in all_data
                    and condition in all_data[workload]
                    and app in all_data[workload][condition]
                ):
                    satisfaction_rate = all_data[workload][condition][app]

                # Calculate x position for this bar
                x_pos = (
                    condition_base
                    + app_idx * (bar_width + app_spacing)
                    + 0.5 * bar_width
                )

                # Plot bar
                plt.bar(
                    x_pos,
                    satisfaction_rate,
                    width=bar_width,
                    color=app_colors[app],
                    alpha=0.8,
                    edgecolor="black",
                    linewidth=1.2,
                    label=app if workload_idx == 0 and cond_idx == 0 else "",
                )

    # Prepare x-axis labels and positions
    x_positions = []
    x_labels = []

    for workload_idx, workload in enumerate(workloads):
        workload_base = workload_base_positions[workload_idx]

        for cond_idx, condition in enumerate(conditions):
            condition_base = workload_base + cond_idx * (
                condition_group_width + condition_spacing
            )

            # Center position (middle of AR bar at index 1)
            middle_bar_pos = (
                condition_base + 1 * (bar_width + app_spacing) + bar_width / 2
            )
            x_positions.append(middle_bar_pos)

            # Create label
            workload_short = "Static" if workload == "static" else "Dynamic"
            condition_label = "w/ Drop" if condition == "drop" else "w/o Drop"
            x_labels.append(f"{condition_label}\n{workload_short}")

    # Customize the plot
    plt.ylabel(
        "SLO Satisfaction\nRate (%)",
        fontsize=40,
        fontweight="500",
        color="#2c3e50",
    )

    # Set x-axis labels
    plt.xticks(x_positions, x_labels, fontsize=32, color="#2c3e50")

    # Add vertical separators between workload groups
    for workload_idx in range(1, n_workloads):
        separator_x = (
            workload_base_positions[workload_idx] - workload_spacing / 2
        )
        plt.axvline(
            x=separator_x, color="gray", linestyle="--", alpha=0.5, linewidth=2
        )

    # Set y-axis limits and styling
    plt.ylim(0, 115)
    plt.yticks([0, 50, 100])
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=40,
        colors="#2c3e50",
        width=1.5,
        length=8,
    )
    plt.tick_params(
        axis="x",
        which="major",
        labelsize=38,
        colors="#2c3e50",
        width=1.5,
        length=8,
        pad=10,
    )

    # Enhanced grid
    plt.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, color="#bdc3c7")

    # Add legend at the top center
    plt.legend(
        fontsize=38,
        frameon=False,
        bbox_to_anchor=(0.5, 1.1),
        loc="upper center",
        ncol=3,
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

    # Save the plot (PDF only)
    output_path_pdf = os.path.join(output_dir, "figure_21.pdf")
    plt.savefig(
        output_path_pdf, dpi=300, bbox_inches="tight", facecolor="white"
    )

    print(f"\nFigure 21 saved as: {output_path_pdf}")

    plt.close()
