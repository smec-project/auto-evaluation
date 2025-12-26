import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re
import glob
from typing import Tuple
import matplotlib.ticker as ticker


def extract_data_size(filename):
    """Extract data size from filename (format: udp_latency_bytesXXXXX_YYYYMMDD_HHMMSS.txt or ul_udp_bytesXXXXX_YYYYMMDD_HHMMSS.txt)"""
    match = re.search(r"bytes(\d+)", os.path.basename(filename))
    if match:
        return int(match.group(1))
    return 0


def filter_data(df, filename, is_uplink=False):
    """Filter data and calculate total latency"""
    if df is None or df.empty:
        print(f"No data to filter for {filename}")
        return None

    sync_rtt_median = df["sync_rtt_ms"].median()
    print(f"File: {filename}, Median sync_rtt_ms: {sync_rtt_median:.4f}ms")

    filtered_data = df.copy()

    sync_rtt_deviation = (filtered_data["sync_rtt_ms"] - sync_rtt_median) / 2

    filtered_data["duration_adjusted_ms"] = filtered_data.apply(
        lambda row: 0.0 if row["data_size"] < 1500 else row["duration_ms"],
        axis=1,
    )

    if is_uplink:
        filtered_data["total_ms"] = (
            filtered_data["ul_delay_ms"]
            + filtered_data["duration_adjusted_ms"]
            - sync_rtt_deviation
        )
    else:
        filtered_data["dl_delay_adjusted_ms"] = filtered_data["dl_delay_ms"]
        filtered_data["total_ms"] = (
            filtered_data["total_ms"] - sync_rtt_deviation
        )

    print(f"File: {filename}, Data points: {len(filtered_data)}")

    return filtered_data


def process_directory(directory_path):
    """Read and process data from a directory"""
    file_pattern = os.path.join(directory_path, "*.txt")
    files = glob.glob(file_pattern)
    processed_data_frames = []

    is_uplink = "ul" in os.path.basename(directory_path)

    for file in files:
        try:
            with open(file, "r") as f:
                lines = f.readlines()

            data_lines = lines[2:]

            data = []
            for line in data_lines:
                if line.strip():
                    parts = line.split()
                    if is_uplink and len(parts) >= 5:
                        data.append(
                            {
                                "index": parts[0],
                                "ul_delay_ms": float(parts[1]),
                                "duration_ms": float(parts[2]),
                                "packet_size": int(parts[3]),
                                "sync_rtt_ms": float(parts[4]),
                            }
                        )
                    elif not is_uplink and len(parts) >= 7:
                        data.append(
                            {
                                "index": parts[0],
                                "dl_delay_ms": float(parts[1]),
                                "time_diff_ms": float(parts[2]),
                                "duration_ms": float(parts[3]),
                                "total_ms": float(parts[4]),
                                "packet_size": int(parts[5]),
                                "sync_rtt_ms": float(parts[6]),
                            }
                        )

            df = pd.DataFrame(data)

            data_size = extract_data_size(file)
            df["data_size"] = data_size

            df["directory"] = os.path.basename(directory_path)

            print(
                f"Processing file: {file}, data size: {data_size} bytes, rows:"
                f" {len(df)}"
            )

            filtered_df = filter_data(df, file, is_uplink)

            if filtered_df is not None and not filtered_df.empty:
                processed_data_frames.append(filtered_df)
                print(
                    f"File: {file}, rows after processing: {len(filtered_df)}"
                )

        except Exception as e:
            print(f"Error processing file {file}: {e}")

    if processed_data_frames:
        combined_df = pd.concat(processed_data_frames, ignore_index=True)
        return combined_df

    return None


def create_total_latency_boxplot(all_data, output_file="total_latency_boxplot"):
    """Create box plots for total latency"""
    if not all_data:
        print("No data to plot")
        return

    plt.rcParams.update({"font.size": 18})

    all_sizes = set()
    for data in all_data.values():
        all_sizes.update(data["data_size"].unique())
    data_sizes = sorted(all_sizes)

    fig, ax = plt.subplots(figsize=(16, 6))

    colors = ["#1f77b4", "#ff7f0e"]

    directory_order = ["dl", "ul"]

    boxprops = dict(linewidth=2.0)
    whiskerprops = dict(linewidth=2.0)
    capprops = dict(linewidth=2.0)
    medianprops = dict(color="black", linewidth=2.0)

    box_width = 0.25
    group_spacing = 1.0

    legend_labels = {"dl": "Downlink", "ul": "Uplink"}

    legend_handles = []
    max_whisker = 0

    for size_idx, size in enumerate(data_sizes):
        base_position = size_idx * group_spacing

        for dir_idx, directory in enumerate(directory_order):
            if directory in all_data:
                dir_data = all_data[directory]
                size_data = dir_data[dir_data["data_size"] == size]

                if not size_data.empty:
                    total_latency = size_data["total_ms"].dropna().values

                    if len(total_latency) > 0:
                        q1 = pd.Series(total_latency).quantile(0.25)
                        q3 = pd.Series(total_latency).quantile(0.75)
                        iqr = q3 - q1
                        upper_whisker = min(total_latency.max(), q3 + 1.5 * iqr)
                        max_whisker = max(max_whisker, upper_whisker)

                    position = base_position + (dir_idx - 0.5) * box_width * 0.8

                    bp = ax.boxplot(
                        total_latency,
                        positions=[position],
                        widths=box_width * 0.8,
                        boxprops=boxprops,
                        whiskerprops=whiskerprops,
                        capprops=capprops,
                        medianprops=medianprops,
                        patch_artist=True,
                        showfliers=False,
                    )

                    for box in bp["boxes"]:
                        box.set(facecolor=colors[dir_idx], alpha=0.8)

                    if size_idx == 0:
                        legend_handles.append(
                            plt.Rectangle(
                                (0, 0),
                                1,
                                1,
                                fc=colors[dir_idx],
                                alpha=0.8,
                                label=legend_labels[directory],
                            )
                        )

    def format_size_label(size):
        if size >= 1000000:
            return f"{size/1000000:.1f}"
        elif size >= 1000:
            return f"{size/1000:.0f}"
        else:
            return f"{size} B"

    ax.set_xticks([i * group_spacing for i in range(len(data_sizes))])
    ax.set_xticklabels([format_size_label(size) for size in data_sizes])

    ax.set_xlabel("Data Size (KB)", fontsize=42)
    ax.set_ylabel("Latency (ms)", fontsize=42)

    ax.legend(
        handles=legend_handles,
        loc="upper center",
        fontsize=38,
        ncol=2,
        frameon=False,
    )

    ax.grid(True, linestyle="--", alpha=0.3)

    if max_whisker > 150:
        ax.set_ylim(0, 200)
        ax.set_yticks([0, 50, 100, 150, 200])
    else:
        ax.set_ylim(0, 150)
        ax.set_yticks([0, 50, 100, 150])

    ax.tick_params(axis="x", which="major", labelsize=42)
    ax.tick_params(axis="y", which="major", labelsize=42)

    plt.tight_layout()
    plt.savefig(output_file + ".pdf", format="pdf", bbox_inches="tight")
    print(f"Total latency box plot saved to {output_file}.pdf")

    plt.close("all")


def generate_latency_decomposition_figure(
    data_path, label, output_dir="figures"
):
    """
    Generate latency decomposition figure for a given city.

    Args:
        data_path: Path to the city directory containing 'ul' and 'dl' subdirectories
                  e.g., '/path/to/measurements/latency-decomposition/Dallas'
        label: Label for the figure, e.g., 'figure 2', 'figure 28a', 'figure 28b'
        output_dir: Directory to save the output figure (default: 'figures')

    Returns:
        Path to the generated PDF file
    """
    print(f"\n{'='*60}")
    print(f"Generating {label} for {os.path.basename(data_path)}")
    print(f"{'='*60}")

    os.makedirs(output_dir, exist_ok=True)

    directories = ["dl", "ul"]

    all_data = {}
    for directory in directories:
        dir_path = os.path.join(data_path, directory)
        if os.path.exists(dir_path):
            print(f"\nProcessing directory: {dir_path}")
            dir_data = process_directory(dir_path)
            if dir_data is not None and not dir_data.empty:
                all_data[directory] = dir_data
                print(
                    f"Directory {directory}: {len(dir_data)} total data points"
                )
        else:
            print(f"Directory {dir_path} not found")

    output_file = os.path.join(output_dir, f"figure_{label}")
    create_total_latency_boxplot(all_data, output_file)

    return output_file + ".pdf"


def extract_timestamp_from_filename(filename: str) -> str:
    """
    Extract timestamp from filename for matching purpose.
    Args:
        filename: File name like 'latency_20250530_053530833.txt'
    Returns:
        Timestamp string for matching (e.g., '20250530_0535')
    """
    match = re.search(r"(\d{8})_(\d{2})(\d{2})\d+", filename)
    if match:
        date_part = match.group(1)
        hour_part = match.group(2)
        minute_part = match.group(3)
        return f"{date_part}_{hour_part}{minute_part}"
    return ""


def find_matching_process_file(latency_file: str, process_files: list) -> str:
    """
    Find the corresponding process file for a given latency file.
    Args:
        latency_file: Name of the latency file
        process_files: List of available process files
    Returns:
        Matching process file name or empty string if not found
    """
    latency_timestamp = extract_timestamp_from_filename(latency_file)
    if not latency_timestamp:
        return ""

    for process_file in process_files:
        process_timestamp = extract_timestamp_from_filename(process_file)
        if latency_timestamp[-2:] == process_timestamp[-2:]:
            return process_file
    return ""


def load_e2e_latency_data(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load E2E latency data from file.
    Args:
        file_path: Path to the latency file
    Returns:
        Tuple of (frame_indices, latency_values) for valid data
    """
    data = []
    frame_indices = []

    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        line = line.strip()
        if line:
            try:
                parts = line.split()
                frame_num = int(parts[0])
                latency_str = parts[1].replace("ms", "").strip()
                latency_val = float(latency_str)

                frame_indices.append(frame_num)
                data.append(latency_val)
            except (ValueError, IndexError):
                continue

    return np.array(frame_indices), np.array(data)


def load_processing_data(
    file_path: str, valid_frame_indices: np.ndarray
) -> np.ndarray:
    """
    Load processing time data from process file, filtering by valid frame indices.
    Args:
        file_path: Path to the process file
        valid_frame_indices: Frame indices that have valid E2E data
    Returns:
        Processing time values for valid frames
    """
    processing_data = []

    with open(file_path, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        line = line.strip()
        if line:
            try:
                parts = line.split()
                frame_num = int(parts[0])

                if frame_num in valid_frame_indices:
                    processing_time = float(parts[1])
                    processing_data.append(processing_time)
            except (ValueError, IndexError):
                continue

    return np.array(processing_data)


def calculate_cdf(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate CDF for given data.
    Args:
        data: Input data array
    Returns:
        Tuple of (sorted_data, cdf_values)
    """
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf


def process_folder_data(
    result_folder: str, process_folder: str
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Process all files in a folder pair and return combined E2E, processing, and network latency data.
    Args:
        result_folder: Path to result folder containing latency files
        process_folder: Path to process folder containing processing time files
    Returns:
        Tuple of (combined_e2e_data, combined_processing_data, combined_network_data)
    """
    e2e_all_data = []
    processing_all_data = []
    network_all_data = []

    latency_files = [
        f
        for f in os.listdir(result_folder)
        if f.endswith(".txt") and f.startswith("latency_")
    ]
    process_files = [
        f
        for f in os.listdir(process_folder)
        if f.endswith(".txt") and f.startswith("process_")
    ]

    print(
        f"Processing {len(latency_files)} latency files from"
        f" {os.path.basename(result_folder)}"
    )

    for latency_file in latency_files:
        matching_process_file = find_matching_process_file(
            latency_file, process_files
        )

        if not matching_process_file:
            print(f"Warning: No matching process file found for {latency_file}")
            continue

        latency_path = os.path.join(result_folder, latency_file)
        frame_indices, e2e_data = load_e2e_latency_data(latency_path)

        if len(e2e_data) == 0:
            print(f"Warning: No valid E2E data in {latency_file}")
            continue

        process_path = os.path.join(process_folder, matching_process_file)
        processing_data = load_processing_data(process_path, frame_indices)

        if len(processing_data) != len(e2e_data):
            print(
                f"Warning: Mismatched data lengths for {latency_file}:"
                f" E2E={len(e2e_data)}, Processing={len(processing_data)}"
            )
            min_len = min(len(e2e_data), len(processing_data))
            e2e_data = e2e_data[:min_len]
            processing_data = processing_data[:min_len]

        network_data = e2e_data - processing_data

        e2e_all_data.extend(e2e_data)
        processing_all_data.extend(processing_data)
        network_all_data.extend(network_data)

        print(
            f"  Processed {latency_file} -> {matching_process_file}:"
            f" {len(e2e_data)} data points"
        )

    return (
        np.array(e2e_all_data),
        np.array(processing_all_data),
        np.array(network_all_data),
    )


def generate_e2e_cdf_figure(data_path, label, output_dir="figures"):
    """
    Generate E2E latency CDF figure for a given task type.

    Args:
        data_path: Path to the task directory containing city subdirectories
                  e.g., '/path/to/measurements/e2e-results/ar'
        label: Label for the figure, e.g., '1', '22'
        output_dir: Directory to save the output figure (default: 'figures')

    Returns:
        Path to the generated PDF file
    """
    print(f"\n{'='*60}")
    print(f"Generating Figure {label} for {os.path.basename(data_path)}")
    print(f"{'='*60}")

    os.makedirs(output_dir, exist_ok=True)

    folder_pairs = [
        (
            os.path.join(data_path, "Dallas/result-nostress"),
            os.path.join(data_path, "Dallas/result-process-nostress"),
            "City-1",
        ),
        (
            os.path.join(data_path, "Dallas/result-busy"),
            os.path.join(data_path, "Dallas/result-process-busy"),
            "City-1-Busy",
        ),
        (
            os.path.join(data_path, "Nanjing/result-nostress"),
            os.path.join(data_path, "Nanjing/result-process-nostress"),
            "City-2",
        ),
        (
            os.path.join(data_path, "Seoul/result-nostress"),
            os.path.join(data_path, "Seoul/result-process-nostress"),
            "City-3",
        ),
    ]

    plt.rcParams.update(
        {
            "font.size": 20,
            "axes.labelsize": 24,
            "axes.titlesize": 26,
            "xtick.labelsize": 24,
            "ytick.labelsize": 26,
            "legend.fontsize": 18,
            "figure.titlesize": 28,
            "lines.linewidth": 3,
            "xtick.major.size": 12,
            "ytick.major.size": 12,
        }
    )

    all_e2e_data = {}
    all_processing_data = {}
    all_network_data = {}

    for result_folder, process_folder, city_label in folder_pairs:
        if not os.path.exists(result_folder) or not os.path.exists(
            process_folder
        ):
            print(
                f"Warning: Folder pair {result_folder}/{process_folder} not"
                " found, skipping..."
            )
            continue

        print(f"\nProcessing folder pair: {city_label}")
        e2e_data, processing_data, network_data = process_folder_data(
            result_folder, process_folder
        )

        if (
            len(e2e_data) > 0
            and len(processing_data) > 0
            and len(network_data) > 0
        ):
            all_e2e_data[city_label] = e2e_data
            all_processing_data[city_label] = processing_data
            all_network_data[city_label] = network_data
            print(
                f"  Total data points for {city_label}: E2E={len(e2e_data)},"
                f" Processing={len(processing_data)},"
                f" Network={len(network_data)}"
            )
        else:
            print(f"  No valid data found for {city_label}")

    plt.figure(figsize=(18, 7))

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd"]
    linestyles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "v"]

    for i, (city_label, data) in enumerate(all_e2e_data.items()):
        if len(data) > 0:
            sorted_data, cdf = calculate_cdf(data)
            plt.plot(
                sorted_data,
                cdf,
                label=city_label,
                color=colors[i % len(colors)],
                linestyle=linestyles[i % len(linestyles)],
                marker=markers[i % len(markers)],
                markersize=12,
                markevery=len(sorted_data) // 20,
                linewidth=6,
                alpha=0.9,
                markerfacecolor="white",
                markeredgewidth=3,
                markeredgecolor=colors[i % len(colors)],
            )

    plt.axvline(
        x=100, color="#d62728", linestyle=":", linewidth=6, alpha=0.8, zorder=5
    )

    plt.xlabel("E2E Latency (ms)", fontsize=52, color="#333333")
    plt.ylabel("CDF", fontsize=52, color="#333333")

    handles, labels_list = plt.gca().get_legend_handles_labels()
    slo_line = plt.Line2D(
        [0], [0], color="#d62728", linestyle=":", linewidth=6, alpha=0.8
    )
    handles.append(slo_line)
    labels_list.append("SLO")

    plt.legend(
        handles,
        labels_list,
        fontsize=36,
        frameon=True,
        fancybox=True,
        shadow=True,
        bbox_to_anchor=(0.5, 1.02),
        loc="lower center",
        ncol=5,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
        columnspacing=1.0,
        handletextpad=0.4,
    )

    plt.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")

    plt.ylim(0, 1.05)
    plt.yticks([0, 0.5, 1])
    plt.xscale("log")
    plt.xlim(left=30)

    plt.gca().xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=6))
    plt.gca().xaxis.set_minor_locator(
        ticker.LogLocator(base=10, subs=(0.2, 0.4, 0.6, 0.8), numticks=12)
    )

    plt.tick_params(
        axis="x",
        which="major",
        labelsize=52,
        colors="#333333",
        width=2,
        length=10,
    )
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=52,
        colors="#333333",
        width=2,
        length=10,
    )

    plt.gca().set_facecolor("#fafafa")

    for spine in plt.gca().spines.values():
        spine.set_linewidth(2.5)
        spine.set_color("#333333")

    plt.tight_layout()

    output_file = os.path.join(output_dir, f"figure_{label}.pdf")
    plt.savefig(output_file, format="pdf", dpi=300, bbox_inches="tight")
    print(f"\nE2E latency CDF plot saved as '{output_file}'")
    plt.close()

    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    slo_threshold = 100

    print(f"\nSLO COMPLIANCE (< {slo_threshold}ms):")
    print("-" * 40)

    for city_label in all_e2e_data.keys():
        if (
            city_label in all_e2e_data
            and city_label in all_processing_data
            and city_label in all_network_data
        ):
            e2e_data = all_e2e_data[city_label]
            processing_data = all_processing_data[city_label]
            network_data = all_network_data[city_label]

            e2e_below_slo = np.sum(e2e_data < slo_threshold)
            e2e_total = len(e2e_data)
            e2e_slo_ratio = e2e_below_slo / e2e_total

            print(
                f"{city_label}:"
                f" {e2e_slo_ratio:.4f} ({e2e_below_slo}/{e2e_total})"
            )

            print(f"\n{city_label}:")
            print(
                f"  E2E Latency     - Mean: {np.mean(e2e_data):.2f}ms, Median:"
                f" {np.median(e2e_data):.2f}ms, 95th percentile:"
                f" {np.percentile(e2e_data, 95):.2f}ms"
            )
            print(
                f"  Processing Time - Mean: {np.mean(processing_data):.2f}ms,"
                f" Median: {np.median(processing_data):.2f}ms, 95th percentile:"
                f" {np.percentile(processing_data, 95):.2f}ms"
            )
            print(
                f"  Network Latency - Mean: {np.mean(network_data):.2f}ms,"
                f" Median: {np.median(network_data):.2f}ms, 95th percentile:"
                f" {np.percentile(network_data, 95):.2f}ms"
            )

    return output_file


def generate_compute_contention_cdf_figure(
    app_type, city, label, output_dir="figures"
):
    """
    Generate compute contention E2E latency CDF figure for a given app and city.

    Args:
        app_type: Application type ('ar' or 'ss')
        city: City name ('Dallas', 'Nanjing', or 'Seoul')
        label: Label for the figure, e.g., '4', '23', '24', '25', '26', '27'
        output_dir: Directory to save the output figure (default: 'figures')

    Returns:
        Path to the generated PDF file
    """
    print(f"\n{'='*60}")
    print(
        f"Generating Figure {label} for {app_type.upper()} in {city} (Compute"
        " Contention)"
    )
    print(f"{'='*60}")

    os.makedirs(output_dir, exist_ok=True)

    base_path = f"measurements/e2e-results-compute-contention/{app_type}/{city}"

    if app_type == "ar":
        folder_pairs = [
            ("result-nostress", "results-process-nostress", "0%"),
            ("result-sm-20", "results-process-sm-20", "20%"),
            ("result-sm-40", "results-process-sm-40", "40%"),
            ("result-sm-60", "results-process-sm-60", "60%"),
        ]
    elif app_type == "ss":
        folder_pairs = [
            ("result-nostress", "result-process-nostress", "0%"),
            ("result-cpu-10", "result-process-cpu-10", "10%"),
            ("result-cpu-20", "result-process-cpu-20", "20%"),
            ("result-cpu-30", "result-process-cpu-30", "30%"),
            ("result-cpu-40", "result-process-cpu-40", "40%"),
        ]
    else:
        raise ValueError(f"Unknown app_type: {app_type}. Must be 'ar' or 'ss'.")

    plt.rcParams.update(
        {
            "font.size": 20,
            "axes.labelsize": 24,
            "axes.titlesize": 26,
            "xtick.labelsize": 24,
            "ytick.labelsize": 26,
            "legend.fontsize": 20,
            "figure.titlesize": 28,
            "lines.linewidth": 3,
            "xtick.major.size": 8,
            "ytick.major.size": 8,
        }
    )

    all_e2e_data = {}
    all_processing_data = {}
    all_network_data = {}

    for result_folder, process_folder, contention_label in folder_pairs:
        result_path = os.path.join(base_path, result_folder)
        process_path = os.path.join(base_path, process_folder)

        if not os.path.exists(result_path) or not os.path.exists(process_path):
            print(
                f"Warning: Folder pair {result_path}/{process_path} not found,"
                " skipping..."
            )
            continue

        print(f"\nProcessing contention level: {contention_label}")
        e2e_data, processing_data, network_data = process_folder_data(
            result_path, process_path
        )

        if (
            len(e2e_data) > 0
            and len(processing_data) > 0
            and len(network_data) > 0
        ):
            all_e2e_data[contention_label] = e2e_data
            all_processing_data[contention_label] = processing_data
            all_network_data[contention_label] = network_data
            print(
                f"  Total data points for {contention_label}:"
                f" E2E={len(e2e_data)}, Processing={len(processing_data)},"
                f" Network={len(network_data)}"
            )
        else:
            print(f"  No valid data found for {contention_label}")

    plt.figure(figsize=(20, 8))

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except:
        try:
            plt.style.use("seaborn-whitegrid")
        except:
            pass

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#8B4513",
        "#9467bd",
    ]
    linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]
    markers = ["o", "s", "^", "D", "v"]

    for i, (contention_label, data) in enumerate(all_e2e_data.items()):
        if len(data) > 0:
            sorted_data, cdf = calculate_cdf(data)
            plt.plot(
                sorted_data,
                cdf,
                label=contention_label,
                color=colors[i % len(colors)],
                linestyle=linestyles[i % len(linestyles)],
                marker=markers[i % len(markers)],
                markersize=12,
                markevery=len(sorted_data) // 20,
                linewidth=6,
                alpha=0.9,
                markerfacecolor="white",
                markeredgewidth=3,
                markeredgecolor=colors[i % len(colors)],
            )

    plt.axvline(
        x=100, color="#d62728", linestyle=":", linewidth=6, alpha=0.8, zorder=5
    )

    plt.xlabel("E2E Latency (ms)", fontsize=52, color="#333333")
    plt.ylabel("CDF", fontsize=52, color="#333333")

    handles, labels_list = plt.gca().get_legend_handles_labels()
    slo_line = plt.Line2D(
        [0], [0], color="#d62728", linestyle=":", linewidth=6, alpha=0.8
    )
    handles.append(slo_line)
    labels_list.append("SLO")

    plt.legend(
        handles,
        labels_list,
        fontsize=40,
        frameon=True,
        fancybox=True,
        shadow=True,
        bbox_to_anchor=(0.5, 1.02),
        loc="lower center",
        ncol=6,
        framealpha=0.95,
        edgecolor="#333333",
        facecolor="white",
        columnspacing=1.0,
        handletextpad=0.4,
    )

    plt.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, color="#cccccc")

    plt.ylim(0, 1.05)
    plt.yticks([0, 0.5, 1])
    plt.xscale("log")
    plt.xlim(left=40)

    plt.gca().xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=6))
    plt.gca().xaxis.set_minor_locator(
        ticker.LogLocator(base=10, subs=(0.2, 0.4, 0.6, 0.8), numticks=12)
    )

    plt.tick_params(
        axis="x",
        which="major",
        labelsize=52,
        colors="#333333",
        width=2,
        length=10,
    )
    plt.tick_params(
        axis="y",
        which="major",
        labelsize=52,
        colors="#333333",
        width=2,
        length=10,
    )

    plt.gca().set_facecolor("#fafafa")

    for spine in plt.gca().spines.values():
        spine.set_linewidth(2.5)
        spine.set_color("#333333")

    plt.tight_layout()

    output_file = os.path.join(output_dir, f"figure_{label}.pdf")
    plt.savefig(output_file, format="pdf", dpi=300, bbox_inches="tight")
    print(f"\nCompute contention CDF plot saved as '{output_file}'")
    plt.close()

    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    slo_threshold = 100

    print(f"\nSLO COMPLIANCE (< {slo_threshold}ms):")
    print("-" * 40)

    for contention_label in all_e2e_data.keys():
        if (
            contention_label in all_e2e_data
            and contention_label in all_processing_data
            and contention_label in all_network_data
        ):
            e2e_data = all_e2e_data[contention_label]
            processing_data = all_processing_data[contention_label]
            network_data = all_network_data[contention_label]

            e2e_below_slo = np.sum(e2e_data < slo_threshold)
            e2e_total = len(e2e_data)
            e2e_slo_ratio = e2e_below_slo / e2e_total

            print(
                f"{contention_label}:"
                f" {e2e_slo_ratio:.4f} ({e2e_below_slo}/{e2e_total})"
            )

            print(f"\n{contention_label}:")
            print(
                f"  E2E Latency     - Mean: {np.mean(e2e_data):.2f}ms, Median:"
                f" {np.median(e2e_data):.2f}ms, 95th percentile:"
                f" {np.percentile(e2e_data, 95):.2f}ms"
            )
            print(
                f"  Processing Time - Mean: {np.mean(processing_data):.2f}ms,"
                f" Median: {np.median(processing_data):.2f}ms, 95th percentile:"
                f" {np.percentile(processing_data, 95):.2f}ms"
            )
            print(
                f"  Network Latency - Mean: {np.mean(network_data):.2f}ms,"
                f" Median: {np.median(network_data):.2f}ms, 95th percentile:"
                f" {np.percentile(network_data, 95):.2f}ms"
            )

    return output_file
