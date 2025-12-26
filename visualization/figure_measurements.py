import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import glob


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
