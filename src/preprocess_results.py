#!/usr/bin/env python3
"""
Preprocess results to extract remaining time information from controller logs.
"""

import re
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class SentEvent:
    timestamp: float
    request_id: int


@dataclass
class AddedEvent:
    timestamp: float
    request_id: int
    remaining_time: float
    slo_latency: float


@dataclass
class ProcessedEvent:
    ue_id: str
    sent_timestamp: float
    added_timestamp: float
    request_id: int
    remaining_time: float
    slo_latency: float


def parse_controller_log(log_file_path: str) -> Dict[str, List[ProcessedEvent]]:
    """
    Parse the controller log file and extract processed events for each UE.

    Args:
        log_file_path: Path to controller.log file

    Returns:
        Dictionary mapping UE IDs to lists of processed events
    """
    # Store events by UE
    ue_sent_events: Dict[str, List[SentEvent]] = defaultdict(list)
    ue_added_events: Dict[str, List[AddedEvent]] = defaultdict(list)

    # Regex patterns
    sent_pattern = r"\[(\d+\.\d+)\] (ue\d+) sent request (\d+) at"
    added_pattern = (
        r"\[(\d+\.\d+)\] (ue\d+) added request (\d+), Remaining time: ([\d.]+)"
        r" ms, SLO latency: ([\d.]+) ms"
    )

    with open(log_file_path, "r") as f:
        for line in f:
            # Check for sent events
            sent_match = re.search(sent_pattern, line)
            if sent_match:
                timestamp = float(sent_match.group(1))
                ue_id = sent_match.group(2)
                request_id = int(sent_match.group(3))
                ue_sent_events[ue_id].append(SentEvent(timestamp, request_id))
                continue

            # Check for added events
            added_match = re.search(added_pattern, line)
            if added_match:
                timestamp = float(added_match.group(1))
                ue_id = added_match.group(2)
                request_id = int(added_match.group(3))
                remaining_time = float(added_match.group(4))
                slo_latency = float(added_match.group(5))
                ue_added_events[ue_id].append(
                    AddedEvent(
                        timestamp, request_id, remaining_time, slo_latency
                    )
                )

    return process_ue_events(ue_sent_events, ue_added_events)


def process_ue_events(
    ue_sent_events: Dict[str, List[SentEvent]],
    ue_added_events: Dict[str, List[AddedEvent]],
) -> Dict[str, List[ProcessedEvent]]:
    """Process events for each UE according to the matching logic."""

    processed_events: Dict[str, List[ProcessedEvent]] = defaultdict(list)

    for ue_id in ue_added_events.keys():
        sent_events = sorted(ue_sent_events[ue_id], key=lambda x: x.timestamp)
        added_events = sorted(ue_added_events[ue_id], key=lambda x: x.timestamp)

        if not added_events:
            continue

        # Process each added event
        for added_event in added_events:
            # Calculate ground truth start time: added_time - SLO + remaining_time
            # Convert ms to seconds for calculation
            slo_seconds = added_event.slo_latency / 1000.0
            remaining_seconds = added_event.remaining_time / 1000.0
            ground_truth_start = (
                added_event.timestamp - slo_seconds + remaining_seconds
            )

            # Find the sent event closest to the ground truth start time
            matching_sent = find_closest_sent_event(
                sent_events, ground_truth_start
            )

            if matching_sent:
                processed_event = ProcessedEvent(
                    ue_id=ue_id,
                    sent_timestamp=matching_sent.timestamp,
                    added_timestamp=added_event.timestamp,
                    request_id=matching_sent.request_id,  # Use sent event's request ID
                    remaining_time=added_event.remaining_time,
                    slo_latency=added_event.slo_latency,
                )
                processed_events[ue_id].append(processed_event)

    return processed_events


def find_closest_sent_event(
    sent_events: List[SentEvent],
    target_timestamp: float,
    search_window: int = 5,
) -> Optional[SentEvent]:
    """Find the sent event closest to the target timestamp using binary search."""
    if not sent_events:
        return None

    # Use binary search to find insertion point
    import bisect

    timestamps = [event.timestamp for event in sent_events]
    insertion_point = bisect.bisect_right(timestamps, target_timestamp)

    # Define search range around the insertion point
    start_idx = max(0, insertion_point - search_window)
    end_idx = min(len(sent_events), insertion_point + search_window)

    candidates = sent_events[start_idx:end_idx]

    if not candidates:
        return sent_events[0] if sent_events else None

    # Find the closest one among candidates
    return min(candidates, key=lambda x: abs(x.timestamp - target_timestamp))


def save_processed_events(
    processed_events: Dict[str, List[ProcessedEvent]], base_path: str
):
    """
    Save processed events to separate files in server folders by UE type.

    Args:
        processed_events: Dictionary of processed events by UE
        base_path: Base path to the results directory (e.g., 'results/smec_all_tasks')
    """
    # Define UE categories and their folders
    ue_categories = {
        "ue1": "video-transcoding",
        "ue2": "video-transcoding",
        "ue3": "video-od",
        "ue4": "video-od",
        "ue5": "video-sr",
        "ue6": "video-sr",
    }

    # Save each UE to its corresponding file in the server folder
    for ue_id in sorted(processed_events.keys()):
        if ue_id in ue_categories:
            app_folder = ue_categories[ue_id]
            server_dir = os.path.join(base_path, app_folder, "server")

            # Create server directory if it doesn't exist
            os.makedirs(server_dir, exist_ok=True)

            filename = os.path.join(server_dir, f"remaining_time_{ue_id}.txt")

            with open(filename, "w") as f:
                # Write header with proper alignment
                f.write(f"{'Request':<10} {'Time Diff (us)':<15}\n")

                # Write data for this UE
                for event in processed_events[ue_id]:
                    # Calculate time difference in milliseconds
                    time_diff = (
                        abs(event.added_timestamp - event.sent_timestamp) * 1000
                    )
                    # Calculate error as per the formula
                    slo_remaining_diff = abs(
                        event.slo_latency - event.remaining_time
                    )
                    error = abs(time_diff - slo_remaining_diff)

                    # Convert to microseconds and format with alignment
                    error_us = error * 1000  # Convert ms to us
                    f.write(f"{event.request_id:<10} {error_us:<15.2f}\n")

            print(f"Saved {len(processed_events[ue_id])} events to: {filename}")
        else:
            print(f"Warning: {ue_id} not in category mapping, skipping...")


def preprocess_smec_results(results_dir: str):
    """
    Preprocess SMEC results by extracting remaining time information.

    Args:
        results_dir: Path to the results directory (e.g., 'results/smec_all_tasks')
    """
    controller_log = os.path.join(results_dir, "controller.log")

    if not os.path.exists(controller_log):
        print(f"Error: controller.log not found at {controller_log}")
        return

    print(f"Processing controller log from: {controller_log}")
    processed_events = parse_controller_log(controller_log)

    # Print summary
    print("\nProcessing Summary:")
    print("-" * 40)
    total_events = 0
    for ue_id, events in sorted(processed_events.items()):
        print(f"{ue_id}: {len(events)} processed events")
        total_events += len(events)
    print(f"Total processed events: {total_events}")

    # Save to server folders
    print("\nSaving to server folders...")
    save_processed_events(processed_events, results_dir)

    print("\nPreprocessing complete!")
    print("Files saved in respective server folders:")
    print("- video-transcoding/server/: ue1, ue2")
    print("- video-od/server/: ue3, ue4")
    print("- video-sr/server/: ue5, ue6")
