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


def calculate_network_error_video_transcoding(
    client_dir, server_dir, skip_lines=100, skip_tail=5
):
    """
    Calculate network estimation error for video-transcoding (SS)
    Error = (client_e2e - server_total) - server_estimated_network
    Only keep data where server_estimated_network > 0

    Args:
        client_dir: Directory containing client latency files
        server_dir: Directory containing server process files
        skip_lines: Number of lines to skip from beginning (applied to client)
        skip_tail: Number of lines to skip from end (applied to client)

    Returns:
        list: Network estimation error values
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

    # Match by sorted order
    network_errors = []
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

        # Read client latency data with frame numbers and filter head/tail
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

                # Skip head and tail from client side
                if len(frames) > skip_lines + skip_tail:
                    frames = frames[skip_lines:-skip_tail]
                    latencies = latencies[skip_lines:-skip_tail]

                for frame_num, e2e_latency in zip(frames, latencies):
                    client_data_by_frame[frame_num] = e2e_latency

                print(
                    f"      Client: {len(client_data_by_frame)} frames after"
                    " filtering"
                )
        except Exception as e:
            print(f"    Error reading latency file: {e}")
            continue

        # Read server process data (all data, no filtering on server side)
        server_data_by_frame = {}
        try:
            df = pd.read_csv(matching_process_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 6:
                frame_column = df.iloc[:, 0]
                total_column = df.iloc[:, -2]  # SMEC: second to last is Total
                network_delay_column = df.iloc[
                    :, -1
                ]  # SMEC: last is Network Delay

                for j in range(len(frame_column)):
                    try:
                        frame_num = int(frame_column.iloc[j])
                        total_time = float(
                            str(total_column.iloc[j]).replace("ms", "").strip()
                        )
                        estimated_network = float(
                            str(network_delay_column.iloc[j])
                            .replace("ms", "")
                            .strip()
                        )
                        server_data_by_frame[frame_num] = (
                            total_time,
                            estimated_network,
                        )
                    except (ValueError, AttributeError):
                        continue

                print(f"      Server: {len(server_data_by_frame)} frames total")
        except Exception as e:
            print(f"    Error reading process file: {e}")
            continue

        # Match by frame number and calculate error
        # Only use frames that exist in filtered client data
        matched = 0
        for frame_num, e2e_latency in client_data_by_frame.items():
            if frame_num in server_data_by_frame:
                total_time, estimated_network = server_data_by_frame[frame_num]

                # Only consider if estimated_network > 0
                if estimated_network > 0:
                    # Actual network latency
                    actual_network = e2e_latency - total_time
                    # Error = actual - estimated
                    error = actual_network - estimated_network
                    network_errors.append(error)
                    matched += 1

        print(
            f"    Generated {matched} network error values (estimated_network"
            " > 0)"
        )

    return network_errors


def calculate_network_error_ar_sr(
    client_dir, server_dir, app_type, skip_lines=100, skip_tail=5
):
    """
    Calculate network estimation error for AR/SR applications
    Error = (client_e2e - server_total) - server_estimated_network
    Only keep data where server_estimated_network > 0

    Args:
        client_dir: Directory containing client latency files
        server_dir: Directory containing server process files
        app_type: 'ar' or 'sr'
        skip_lines: Number of lines to skip from beginning (applied to client)
        skip_tail: Number of lines to skip from end (applied to client)

    Returns:
        list: Network estimation error values
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
        client_to_stream[latency_files_with_ts[0][1]] = 0
        client_to_stream[latency_files_with_ts[1][1]] = 1
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

    # Read all server process data (all data, no filtering on server side)
    process_files = glob.glob(os.path.join(server_dir, "process_*.txt"))
    server_data_by_stream_frame = {}

    for process_file in process_files:
        print(f"    Reading process file: {os.path.basename(process_file)}")
        try:
            df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
            if len(df.columns) >= 6:
                stream_column = df.iloc[:, 0]
                frame_column = df.iloc[:, 1]

                # Determine column positions
                is_ar = app_type == "ar"

                if is_ar:
                    # AR: Total at -4, Network Delay at -1
                    total_column = df.iloc[:, -4]
                    network_delay_column = df.iloc[:, -1]
                else:
                    # SR: Total at -3, Network Delay at -1
                    total_column = df.iloc[:, -3]
                    network_delay_column = df.iloc[:, -1]

                for j in range(len(stream_column)):
                    try:
                        stream_id = int(stream_column.iloc[j])
                        frame_num = int(frame_column.iloc[j])
                        total_time = float(
                            str(total_column.iloc[j]).replace("ms", "").strip()
                        )
                        estimated_network = float(
                            str(network_delay_column.iloc[j])
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

                print(
                    "      Extracted"
                    f" {len(server_data_by_stream_frame)} stream-frame pairs"
                )
        except Exception as e:
            print(f"    Error reading {process_file}: {e}")

    # Process each client latency file
    network_errors = []
    for latency_file in client_to_stream.keys():
        stream_id = client_to_stream[latency_file]
        print(
            f"    Processing {os.path.basename(latency_file)} (stream"
            f" {stream_id})..."
        )

        # Read and filter client latency data
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

                # Skip head and tail from client side
                if len(frames) > skip_lines + skip_tail:
                    frames = frames[skip_lines:-skip_tail]
                    latencies = latencies[skip_lines:-skip_tail]

                print(f"      Client: {len(frames)} frames after filtering")

                # Match with server data using filtered client frames
                matched = 0
                for frame_num, e2e_latency in zip(frames, latencies):
                    key = (stream_id, frame_num)
                    if key in server_data_by_stream_frame:
                        total_time, estimated_network = (
                            server_data_by_stream_frame[key]
                        )

                        # Only consider if estimated_network > 0
                        if estimated_network > 0:
                            # Actual network latency
                            actual_network = e2e_latency - total_time
                            # Error = actual - estimated
                            error = actual_network - estimated_network
                            network_errors.append(error)
                            matched += 1

                print(
                    f"      Generated {matched} network error values"
                    " (estimated_network > 0)"
                )
        except Exception as e:
            print(f"      Error reading latency file: {e}")

    return network_errors


def generate_figure_20_a(results_base_path, output_dir):
    """
    Generate Figure 20_a: Network estimation error comparison for static vs dynamic workloads

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

    # Define workloads
    workloads = {
        "smec_all_tasks": "Static",
        "smec_all_tasks_dynamic": "Dynamic",
    }

    # Store all data for plotting
    all_data = {}

    # Process each workload
    for workload_dir, workload_name in workloads.items():
        print(f"\n=== Processing {workload_name} Workload ({workload_dir}) ===")
        all_data[workload_name] = {}

        for app_dir, app_name in applications.items():
            client_path = os.path.join(
                results_base_path, workload_dir, app_dir, "client"
            )
            server_path = os.path.join(
                results_base_path, workload_dir, app_dir, "server"
            )

            if os.path.exists(client_path) and os.path.exists(server_path):
                print(f"  Processing {app_name}...")

                # Calculate network estimation error based on app type
                if app_dir == "video-transcoding":
                    errors = calculate_network_error_video_transcoding(
                        client_path, server_path, skip_lines=100, skip_tail=5
                    )
                elif app_dir == "video-od":
                    errors = calculate_network_error_ar_sr(
                        client_path,
                        server_path,
                        "ar",
                        skip_lines=100,
                        skip_tail=5,
                    )
                else:  # video-sr
                    errors = calculate_network_error_ar_sr(
                        client_path,
                        server_path,
                        "sr",
                        skip_lines=100,
                        skip_tail=5,
                    )

                if errors:
                    all_data[workload_name][app_name] = errors
                    print(f"    Total: {len(errors)} network error values")
                    print(f"    Mean: {np.mean(errors):.2f} ms")
                    print(f"    Median: {np.median(errors):.2f} ms")
                    print(f"    Std: {np.std(errors):.2f} ms")
                else:
                    print(f"    No network error data found")
            else:
                if not os.path.exists(client_path):
                    print(f"  Client directory not found: {client_path}")
                if not os.path.exists(server_path):
                    print(f"  Server directory not found: {server_path}")

    # Create the box plot
    print("\n=== Creating Figure 20_a: Network Estimation Error Box Plot ===")

    plt.figure(figsize=(10, 5.5))

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

    # Define application order and colors
    app_order = ["SS", "AR", "VC"]
    app_colors = {"AR": "#1f77b4", "SS": "#2ca02c", "VC": "#ff7f0e"}

    # Prepare data for grouped box plot
    workload_list = ["Static", "Dynamic"]
    n_workloads = len(workload_list)
    n_apps = len(app_order)

    # Calculate positions for grouped boxes
    box_width = 0.25
    box_spacing = 0.05
    group_spacing = 0.8

    # Create positions for each workload group
    workload_positions = np.arange(n_workloads) * (
        n_apps * (box_width + box_spacing) + group_spacing
    )

    all_positions = []
    all_box_data = []
    all_colors = []

    for i, workload in enumerate(workload_list):
        if workload in all_data:
            workload_data = all_data[workload]

            for j, app in enumerate(app_order):
                if app in workload_data:
                    position = workload_positions[i] + j * (
                        box_width + box_spacing
                    )
                    all_positions.append(position)
                    all_box_data.append(workload_data[app])
                    all_colors.append(app_colors[app])

    # Create the grouped box plot
    box_plot = plt.boxplot(
        all_box_data,
        positions=all_positions,
        widths=box_width,
        patch_artist=True,
        showfliers=False,
    )

    # Color the boxes
    for patch, color in zip(box_plot["boxes"], all_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Style the box plot elements
    for element in ["whiskers", "medians", "caps"]:
        plt.setp(box_plot[element], color="black", linewidth=1.5)

    # Customize the plot
    plt.ylabel("Error (ms)", fontsize=52, fontweight="500", color="#2c3e50")

    # Set x-axis labels at the center of each workload group
    group_centers = (
        workload_positions
        + (n_apps * (box_width + box_spacing) - box_spacing) / 2
    )
    plt.xticks(group_centers, workload_list, fontsize=46, color="#2c3e50")

    # Set y-axis limits and styling
    plt.ylim(-30, 50)
    plt.yticks(np.arange(-25, 50, 25))
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=48,
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

    # Add horizontal line at y=0 for reference
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5, linewidth=1)

    # Enhanced grid
    plt.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, color="#bdc3c7")

    # Create legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=app_colors[app], alpha=0.7, label=app)
        for app in app_order
    ]
    plt.legend(
        handles=legend_elements,
        fontsize=42,
        frameon=False,
        bbox_to_anchor=(0.5, 1.06),
        loc="upper center",
        ncol=2,
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
    output_path_pdf = os.path.join(output_dir, "figure_20_a.pdf")
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white")

    print(f"\nFigure 20_a saved as:")
    print(f"  - {output_path_pdf}")
    plt.close()


def read_remaining_time_file(file_path, skip_lines=100, skip_tail=5):
    """
    Read remaining time data from a single file.

    Args:
        file_path: Path to the remaining_time file
        skip_lines: Number of lines to skip from beginning (default 100)
        skip_tail: Number of lines to skip from end (default 5)

    Returns:
        list: Time diff values in microseconds
    """
    data = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

            # Skip header line and apply filtering
            data_lines = lines[1:]  # Skip header

            # Apply head and tail filtering
            if len(data_lines) > skip_lines + skip_tail:
                data_lines = data_lines[skip_lines:-skip_tail]

            for line in data_lines:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        time_diff_us = float(parts[1])
                        data.append(time_diff_us)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return data


def collect_remaining_time_data(results_base_path):
    """
    Collect remaining time data from all schedulers and applications.

    Args:
        results_base_path: Base path to results directory

    Returns:
        dict: Nested dictionary with structure: scheduler -> workload -> app -> data
    """
    schedulers = ["tutti", "arma", "smec"]
    workloads = ["static", "dynamic"]

    # Application mapping
    app_mapping = {
        "video-transcoding": "SS",
        "video-od": "AR",
        "video-sr": "VC",
    }

    all_data = {}

    for scheduler in schedulers:
        all_data[scheduler] = {}

        for workload in workloads:
            # Construct directory name
            if workload == "static":
                dir_name = f"{scheduler}_all_tasks"
            else:
                dir_name = f"{scheduler}_all_tasks_dynamic"

            results_dir = os.path.join(results_base_path, dir_name)
            all_data[scheduler][workload] = {}

            print(f"\nProcessing {scheduler} - {workload} ({dir_name})...")

            for app_dir, app_name in app_mapping.items():
                server_dir = os.path.join(results_dir, app_dir, "server")

                if not os.path.exists(server_dir):
                    print(f"  Warning: {server_dir} not found")
                    all_data[scheduler][workload][app_name] = []
                    continue

                # Find all remaining_time files
                remaining_files = glob.glob(
                    os.path.join(server_dir, "remaining_time_*.txt")
                )

                app_data = []
                for file_path in remaining_files:
                    file_data = read_remaining_time_file(
                        file_path, skip_lines=100, skip_tail=5
                    )
                    # Convert to milliseconds
                    file_data = [x / 1000.0 for x in file_data]
                    app_data.extend(file_data)

                all_data[scheduler][workload][app_name] = app_data
                print(
                    f"  {app_name}: {len(app_data)} data points from"
                    f" {len(remaining_files)} files"
                )

    return all_data


def generate_figure_19(results_base_path, output_dir):
    """
    Generate Figure 19: Remaining time estimation error P99 comparison

    Args:
        results_base_path: Base path to results directory
        output_dir: Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print("=== Collecting remaining time data ===")
    all_data = collect_remaining_time_data(results_base_path)

    # Check if we have data
    total_data_points = sum(
        len(all_data[scheduler][workload][app])
        for scheduler in all_data
        for workload in all_data[scheduler]
        for app in all_data[scheduler][workload]
    )

    if total_data_points == 0:
        print("No remaining time data found!")
        return

    print(f"\nTotal data points loaded: {total_data_points}")

    # Create the plot
    print("\n=== Creating Figure 19: Remaining Time Error P99 Plot ===")

    schedulers = ["Tutti", "Arma", "SMEC"]
    scheduler_keys = ["tutti", "arma", "smec"]
    applications = ["SS", "AR", "VC"]
    workload_types = ["Static", "Dynamic"]

    # Set up the plot
    plt.figure(figsize=(23, 7))

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

    # Define method styles
    method_styles = {
        "Arma": {"color": "#2ca02c", "label": "ARMA", "hatch": "\\\\"},
        "Tutti": {"color": "#9467bd", "label": "Tutti", "hatch": "---"},
        "SMEC": {"color": "#ff7f0e", "label": "SMEC", "hatch": None},
    }

    # Calculate P99 values
    p99_data = {}
    for scheduler_idx, scheduler_key in enumerate(scheduler_keys):
        p99_data[schedulers[scheduler_idx]] = {}
        for workload_idx, workload in enumerate(["static", "dynamic"]):
            p99_data[schedulers[scheduler_idx]][workload] = {}
            for app in applications:
                data = all_data[scheduler_key][workload][app]
                if data:
                    p99_value = np.percentile(data, 99)
                    p99_data[schedulers[scheduler_idx]][workload][
                        app
                    ] = p99_value
                else:
                    p99_data[schedulers[scheduler_idx]][workload][app] = 0

    # Prepare data for plotting
    n_apps = len(applications)
    n_workloads = len(workload_types)
    n_schedulers = len(schedulers)
    n_groups = n_apps * n_workloads

    bar_width = 0.25
    bar_spacing = 0.02
    group_spacing = 0.8

    # Create x positions
    group_width = n_schedulers * (bar_width + bar_spacing) - bar_spacing
    group_positions = np.arange(n_groups) * (group_width + group_spacing)

    # Plot bars for each scheduler
    for scheduler_idx, scheduler in enumerate(schedulers):
        p99_values = []
        x_positions = []

        group_idx = 0
        for workload_idx, workload in enumerate(["static", "dynamic"]):
            for app in applications:
                p99_value = p99_data[scheduler][workload][app]
                p99_values.append(p99_value)

                x_pos = group_positions[group_idx] + scheduler_idx * (
                    bar_width + bar_spacing
                )
                x_positions.append(x_pos)
                group_idx += 1

        # Plot bars
        plt.bar(
            x_positions,
            p99_values,
            width=bar_width,
            color=method_styles[scheduler]["color"],
            alpha=0.9,
            hatch=method_styles[scheduler]["hatch"],
            edgecolor="black",
            linewidth=1.2,
            label=method_styles[scheduler]["label"],
        )

    # Customize the plot
    plt.ylabel("P99 Error (ms)", fontsize=52, fontweight="500", color="#2c3e50")

    # Set x-axis labels
    group_centers = group_positions + (group_width / 2)

    # Create combined labels
    combined_labels = []
    for workload_idx in range(n_workloads):
        for app in applications:
            combined_labels.append(f"{app}\n{workload_types[workload_idx]}")

    plt.xticks(
        group_centers,
        combined_labels,
        fontsize=38,
        color="#2c3e50",
        ha="center",
    )

    # Set y-axis to log scale
    plt.yscale("log")

    # Set y-axis limits
    current_ylim = plt.ylim()
    plt.ylim(current_ylim[0], current_ylim[1] * 3)

    # Tick styling
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=54,
        colors="#2c3e50",
        width=1.5,
        length=8,
    )
    plt.tick_params(
        axis="y",
        which="minor",
        labelsize=52,
        colors="#2c3e50",
        width=1,
        length=4,
    )
    plt.tick_params(
        axis="x",
        which="major",
        labelsize=52,
        colors="#2c3e50",
        width=1.5,
        length=8,
    )

    # Grid
    plt.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, color="#bdc3c7")

    # Legend
    plt.legend(
        fontsize=50,
        frameon=False,
        bbox_to_anchor=(0.5, 1.09),
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

    # Background color
    plt.gca().set_facecolor("#fafafa")

    plt.tight_layout()

    # Save plot (PDF only)
    output_path_pdf = os.path.join(output_dir, "figure_19.pdf")
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white")

    print(f"\nFigure 19 saved as: {output_path_pdf}")
    plt.close()


if __name__ == "__main__":
    """
    Main function to generate figures
    """
    # Set base path
    results_base_path = "results"
    output_dir = "figures"

    print("=== Generating Figure 20_a: Network Estimation Error ===")
    generate_figure_20_a(results_base_path, output_dir)
    print("\nFigure 20_a generation complete!")

    print("\n" + "=" * 60)
    print("=== Generating Figure 19: Remaining Time Error ===")
    generate_figure_19(results_base_path, output_dir)
    print("\nFigure 19 generation complete!")


def collect_processing_time_differences_ss(
    base_path, skip_lines=100, skip_tail=5
):
    """
    Collect SS (video transcoding) processing time differences.

    Args:
        base_path: Base path to the server directory
        skip_lines: Number of lines to skip from beginning
        skip_tail: Number of lines to skip from end

    Returns:
        list: Processing time differences in milliseconds
    """
    differences = []

    # Find processing and process files (only 2560 for SS)
    processing_files = glob.glob(
        os.path.join(
            base_path, "video-transcoding/server/processing_client*.txt"
        )
    )
    process_files = glob.glob(
        os.path.join(base_path, "video-transcoding/server/process_2560*.txt")
    )

    # Filter for clients 1,2
    processing_files = [
        f for f in processing_files if "client0001" in f or "client0002" in f
    ]
    processing_files.sort()
    process_files.sort()

    print(
        f"  SS: Found {len(processing_files)} processing files and"
        f" {len(process_files)} process files"
    )

    for processing_file, process_file in zip(processing_files, process_files):
        try:
            # Read processing data (expected times)
            processing_df = pd.read_csv(processing_file, sep=r"\s+")
            processing_df.columns = ["frame_index", "processing_time"]

            # Read process data (actual times)
            process_df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
            process_df.columns = [
                "Frame",
                "Decode_Time",
                "Transcode_Time",
                "Encode_Time",
                "Total_Time",
                "Network_Delay",
            ]

            # Merge on frame
            merged = pd.merge(
                processing_df,
                process_df,
                left_on="frame_index",
                right_on="Frame",
                how="inner",
            )

            # Apply filtering: skip head and tail
            if len(merged) > skip_lines + skip_tail:
                merged = merged.iloc[skip_lines:-skip_tail]

            # Calculate difference: expected - actual (in milliseconds)
            merged["expected_ms"] = merged["processing_time"] / 1000
            merged["actual_ms"] = merged["Total_Time"]
            merged["difference"] = merged["expected_ms"] - merged["actual_ms"]

            differences.extend(merged["difference"].tolist())

            print(
                f"    Collected {len(merged)} differences from"
                f" {os.path.basename(processing_file)}"
            )

        except Exception as e:
            print(
                f"    Error processing {os.path.basename(processing_file)}: {e}"
            )

    return differences


def collect_processing_time_differences_ar(
    base_path, skip_lines=100, skip_tail=5
):
    """
    Collect AR processing time differences.

    Args:
        base_path: Base path to the server directory
        skip_lines: Number of lines to skip from beginning
        skip_tail: Number of lines to skip from end

    Returns:
        list: Processing time differences in milliseconds
    """
    differences = []

    # Find processing and process files
    processing_files = glob.glob(
        os.path.join(base_path, "video-od/server/processing_client*.txt")
    )
    process_files = glob.glob(
        os.path.join(base_path, "video-od/server/process_*.txt")
    )

    # Filter for clients 3,4
    processing_files = [
        f for f in processing_files if "client0003" in f or "client0004" in f
    ]
    processing_files.sort()

    print(
        f"  AR: Found {len(processing_files)} processing files and"
        f" {len(process_files)} process files"
    )

    if len(process_files) != 1:
        print("  AR: Expected exactly 1 process file")
        return differences

    try:
        # Read the single process file
        process_file = process_files[0]
        process_df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
        process_df.columns = [
            "Stream",
            "Frame",
            "Network_YOLO",
            "YOLO",
            "YOLO_Response",
            "Total",
            "Detections",
            "CUDA_Priority",
            "Network_Delay",
        ]

        # Get unique stream IDs and sort them
        unique_streams = sorted(process_df["Stream"].unique())

        for i, processing_file in enumerate(processing_files):
            if i >= len(unique_streams):
                break

            try:
                # Read processing data (expected times)
                processing_df = pd.read_csv(processing_file, sep=r"\s+")
                processing_df.columns = ["frame_index", "processing_time"]

                # Get target stream for this client
                target_stream = unique_streams[i]
                stream_process_df = process_df[
                    process_df["Stream"] == target_stream
                ].copy()

                # Merge on frame
                merged = pd.merge(
                    processing_df,
                    stream_process_df,
                    left_on="frame_index",
                    right_on="Frame",
                    how="inner",
                )

                # Apply filtering: skip head and tail
                if len(merged) > skip_lines + skip_tail:
                    merged = merged.iloc[skip_lines:-skip_tail]

                # Calculate difference: expected - actual (in milliseconds)
                merged["expected_ms"] = merged["processing_time"] / 1000
                merged["actual_ms"] = merged["Total"]
                merged["difference"] = (
                    merged["expected_ms"] - merged["actual_ms"]
                )

                differences.extend(merged["difference"].tolist())

                print(
                    f"    Collected {len(merged)} differences from"
                    f" {os.path.basename(processing_file)}"
                )

            except Exception as e:
                print(f"    Error processing AR client {3 + i}: {e}")

    except Exception as e:
        print(f"    Error processing AR data: {e}")

    return differences


def collect_processing_time_differences_vc(
    base_path, skip_lines=100, skip_tail=5
):
    """
    Collect VC (SR) processing time differences.

    Args:
        base_path: Base path to the server directory
        skip_lines: Number of lines to skip from beginning
        skip_tail: Number of lines to skip from end

    Returns:
        list: Processing time differences in milliseconds
    """
    differences = []

    # Find processing and process files
    processing_files = glob.glob(
        os.path.join(base_path, "video-sr/server/processing_client*.txt")
    )
    process_files = glob.glob(
        os.path.join(base_path, "video-sr/server/process_*.txt")
    )

    # Filter for clients 5,6
    processing_files = [
        f for f in processing_files if "client0005" in f or "client0006" in f
    ]
    processing_files.sort()

    print(
        f"  VC: Found {len(processing_files)} processing files and"
        f" {len(process_files)} process files"
    )

    if len(process_files) != 1:
        print("  VC: Expected exactly 1 process file")
        return differences

    try:
        # Read the single process file
        process_file = process_files[0]
        process_df = pd.read_csv(process_file, sep=r"\s+", skiprows=1)
        process_df.columns = [
            "Stream",
            "Frame",
            "Network_SR",
            "SR",
            "SR_Response",
            "Total",
            "Priority",
            "Network_Delay",
        ]

        # Get unique stream IDs and sort them
        unique_streams = sorted(process_df["Stream"].unique())

        for i, processing_file in enumerate(processing_files):
            if i >= len(unique_streams):
                break

            try:
                # Read processing data (expected times)
                processing_df = pd.read_csv(processing_file, sep=r"\s+")
                processing_df.columns = ["frame_index", "processing_time"]

                # Map client to stream
                target_stream = unique_streams[i]
                stream_process_df = process_df[
                    process_df["Stream"] == target_stream
                ].copy()

                # Merge on frame
                merged = pd.merge(
                    processing_df,
                    stream_process_df,
                    left_on="frame_index",
                    right_on="Frame",
                    how="inner",
                )

                # Apply filtering: skip head and tail
                if len(merged) > skip_lines + skip_tail:
                    merged = merged.iloc[skip_lines:-skip_tail]

                # Calculate difference: expected - actual (in milliseconds)
                merged["expected_ms"] = merged["processing_time"] / 1000
                merged["actual_ms"] = merged["Total"]
                merged["difference"] = (
                    merged["expected_ms"] - merged["actual_ms"]
                )

                differences.extend(merged["difference"].tolist())

                print(
                    f"    Collected {len(merged)} differences from"
                    f" {os.path.basename(processing_file)}"
                )

            except Exception as e:
                print(f"    Error processing VC client {5 + i}: {e}")

    except Exception as e:
        print(f"    Error processing VC data: {e}")

    return differences


def generate_figure_20_b(results_base_path, output_dir):
    """
    Generate Figure 20_b: Processing time estimation error comparison

    Args:
        results_base_path: Base path to results directory
        output_dir: Output directory for saving figures
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print("=== Collecting processing time estimation error data ===")

    # Define workloads
    workloads = {
        "smec_all_tasks_disable_32cpu": "Static",
        "smec_all_tasks_dynamic_disable_32cpu": "Dynamic",
    }

    # Define applications
    applications = ["SS", "AR", "VC"]

    # Store all data
    all_data = {}

    for workload_dir, workload_name in workloads.items():
        print(f"\nProcessing {workload_name} Workload ({workload_dir})...")
        workload_path = os.path.join(results_base_path, workload_dir)

        all_data[workload_name] = {}

        # Collect SS data
        print("  Processing SS (video-transcoding)...")
        ss_errors = collect_processing_time_differences_ss(
            workload_path, skip_lines=100, skip_tail=5
        )
        if ss_errors:
            all_data[workload_name]["SS"] = ss_errors
            print(f"    Total: {len(ss_errors)} errors")
            print(f"    Mean: {np.mean(ss_errors):.2f} ms")
            print(f"    Median: {np.median(ss_errors):.2f} ms")

        # Collect AR data
        print("  Processing AR (video-od)...")
        ar_errors = collect_processing_time_differences_ar(
            workload_path, skip_lines=100, skip_tail=5
        )
        if ar_errors:
            all_data[workload_name]["AR"] = ar_errors
            print(f"    Total: {len(ar_errors)} errors")
            print(f"    Mean: {np.mean(ar_errors):.2f} ms")
            print(f"    Median: {np.median(ar_errors):.2f} ms")

        # Collect VC data
        print("  Processing VC (video-sr)...")
        vc_errors = collect_processing_time_differences_vc(
            workload_path, skip_lines=100, skip_tail=5
        )
        if vc_errors:
            all_data[workload_name]["VC"] = vc_errors
            print(f"    Total: {len(vc_errors)} errors")
            print(f"    Mean: {np.mean(vc_errors):.2f} ms")
            print(f"    Median: {np.median(vc_errors):.2f} ms")

    # Create the box plot
    print("\n=== Creating Figure 20_b: Processing Time Error Box Plot ===")

    plt.figure(figsize=(10, 5.5))

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

    # Define application order and colors
    app_order = ["SS", "AR", "VC"]
    app_colors = {"AR": "#1f77b4", "SS": "#2ca02c", "VC": "#ff7f0e"}

    # Prepare data for grouped box plot
    workload_list = ["Static", "Dynamic"]
    n_workloads = len(workload_list)
    n_apps = len(app_order)

    # Calculate positions for grouped boxes
    box_width = 0.25
    box_spacing = 0.05
    group_spacing = 0.8

    # Create positions for each workload group
    workload_positions = np.arange(n_workloads) * (
        n_apps * (box_width + box_spacing) + group_spacing
    )

    all_positions = []
    all_box_data = []
    all_colors = []

    for i, workload in enumerate(workload_list):
        if workload in all_data:
            workload_data = all_data[workload]

            for j, app in enumerate(app_order):
                if app in workload_data:
                    # Filter data to -100 to 100 range for better visualization
                    filtered_data = [
                        x for x in workload_data[app] if -100 <= x <= 100
                    ]

                    if filtered_data:
                        position = workload_positions[i] + j * (
                            box_width + box_spacing
                        )
                        all_positions.append(position)
                        all_box_data.append(filtered_data)
                        all_colors.append(app_colors[app])

    # Create the grouped box plot
    box_plot = plt.boxplot(
        all_box_data,
        positions=all_positions,
        widths=box_width,
        patch_artist=True,
        showfliers=False,
    )

    # Color the boxes
    for patch, color in zip(box_plot["boxes"], all_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Style the box plot elements
    for element in ["whiskers", "medians", "caps"]:
        plt.setp(box_plot[element], color="black", linewidth=1.5)

    # Customize the plot
    plt.ylabel("Error (ms)", fontsize=52, fontweight="500", color="#2c3e50")

    # Set x-axis labels at the center of each workload group
    group_centers = (
        workload_positions
        + (n_apps * (box_width + box_spacing) - box_spacing) / 2
    )
    plt.xticks(group_centers, workload_list, fontsize=46, color="#2c3e50")

    # Set y-axis limits and styling
    plt.ylim(-30, 50)
    plt.yticks(np.arange(-25, 50, 25))
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=48,
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

    # Add horizontal line at y=0 for reference
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.5, linewidth=1)

    # Enhanced grid
    plt.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, color="#bdc3c7")

    # Create legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=app_colors[app], alpha=0.7, label=app)
        for app in app_order
    ]
    plt.legend(
        handles=legend_elements,
        fontsize=42,
        frameon=False,
        bbox_to_anchor=(0.5, 1.06),
        loc="upper center",
        ncol=2,
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
    output_path_pdf = os.path.join(output_dir, "figure_20_b.pdf")
    plt.savefig(output_path_pdf, bbox_inches="tight", facecolor="white")

    print(f"\nFigure 20_b saved as: {output_path_pdf}")
    plt.close()
