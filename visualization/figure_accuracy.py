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
