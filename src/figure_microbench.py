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
