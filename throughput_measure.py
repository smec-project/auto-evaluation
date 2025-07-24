#!/usr/bin/env python3
"""
Throughput Test Script

This script runs network throughput tests using iperf3:
- Starts iperf3 server on edge1
- Runs iperf3 client on amari (in UE namespace)
- Collects and displays results
- Cleans up processes after completion

Usage:
    python throughput_test.py
"""

import logging
import time
import sys
import re
from typing import Dict, Any, Optional
from src.host_manager import HostManager


class ThroughputTest:
    """Throughput test executor using iperf3."""

    def __init__(self, config_file: str = "hosts_config.yaml"):
        """
        Initialize the throughput test.

        Args:
            config_file: Path to the host configuration file
        """
        self.host_manager = HostManager(config_file)
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def start_iperf3_server(self) -> Dict[str, Any]:
        """
        Start iperf3 server on edge1.

        Returns:
            Dictionary containing execution results
        """
        self.logger.info("Starting iperf3 server on edge1...")

        command = "iperf3 -s"

        try:
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=command, session_name="iperf3_server"
            )

            if result["success"]:
                self.logger.info(
                    "✓ iperf3 server started successfully on edge1"
                )
                self.logger.info(
                    f"Session name: {result.get('session_name', 'N/A')}"
                )
            else:
                self.logger.error(
                    f"✗ Failed to start iperf3 server: {result['error']}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during iperf3 server startup: {e}")
            return {
                "success": False,
                "error": str(e),
                "pid": None,
                "output": "",
                "connection_info": "edge1",
            }

    def run_iperf3_client(
        self, ue_namespace: str = "ue1", duration: int = 10, interval: int = 2
    ) -> Dict[str, Any]:
        """
        Run iperf3 client test on amari.

        Args:
            ue_namespace: UE namespace to use (default: ue1)
            duration: Test duration in seconds (default: 10)
            interval: Reporting interval in seconds (default: 2)

        Returns:
            Dictionary containing test results
        """
        self.logger.info(
            f"Running iperf3 client test from {ue_namespace} namespace on"
            " amari..."
        )

        command = (
            f"ip netns exec {ue_namespace} iperf3 -c 192.168.2.3 "
            f"-t {duration} -i {interval}"
        )

        try:
            # Run client test in foreground to capture output
            result = self.host_manager.execute_on_host(
                host_name="amari", command=command, background=False
            )

            if result["success"]:
                self.logger.info("✓ iperf3 client test completed successfully")
            else:
                self.logger.error(
                    "✗ iperf3 client test failed:"
                    f" {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Exception during iperf3 client test: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "exit_code": -1,
            }

    def parse_iperf3_results(self, output: str) -> Dict[str, Any]:
        """
        Parse iperf3 client output to extract throughput results.

        Args:
            output: Raw iperf3 client output

        Returns:
            Dictionary containing parsed results
        """
        results = {
            "total_transferred": None,
            "average_bandwidth": None,
            "average_bandwidth_numeric": None,  # Add numeric value for comparison
            "final_bandwidth": None,
            "intervals": [],
            "raw_output": output,
            "parse_success": False,
            "bandwidth_warning": False,  # Add warning flag
        }

        try:
            lines = output.split("\n")

            # Parse interval results
            interval_pattern = r"\[\s*\d+\]\s+([\d.-]+)-([\d.-]+)\s+sec\s+([\d.]+)\s+([KMGT]?Bytes)\s+([\d.]+)\s+([KMGT]?bits/sec)"

            for line in lines:
                if "sec" in line and "Bytes" in line and "bits/sec" in line:
                    match = re.search(interval_pattern, line)
                    if match:
                        start_time = float(match.group(1))
                        end_time = float(match.group(2))
                        transferred = match.group(3)
                        transferred_unit = match.group(4)
                        bandwidth = match.group(5)
                        bandwidth_unit = match.group(6)

                        results["intervals"].append(
                            {
                                "start_time": start_time,
                                "end_time": end_time,
                                "transferred": (
                                    f"{transferred} {transferred_unit}"
                                ),
                                "bandwidth": f"{bandwidth} {bandwidth_unit}",
                            }
                        )

            # Parse final summary line
            # Example: "[  5]   0.00-10.00  sec  1.12 GBytes   960 Mbits/sec                  receiver"
            summary_pattern = r"\[\s*\d+\]\s+[\d.-]+-([\d.-]+)\s+sec\s+([\d.]+)\s+([KMGT]?Bytes)\s+([\d.]+)\s+([KMGT]?bits/sec).*receiver"

            for line in lines:
                if "receiver" in line:
                    match = re.search(summary_pattern, line)
                    if match:
                        results["total_transferred"] = (
                            f"{match.group(2)} {match.group(3)}"
                        )
                        results["final_bandwidth"] = (
                            f"{match.group(4)} {match.group(5)}"
                        )
                        break

            # Calculate average bandwidth from intervals
            if results["intervals"]:
                # Extract numeric bandwidth values for averaging
                bandwidth_values = []
                for interval in results["intervals"]:
                    bw_str = interval["bandwidth"]
                    # Extract numeric part
                    numeric_match = re.search(r"([\d.]+)", bw_str)
                    if numeric_match:
                        bandwidth_values.append(float(numeric_match.group(1)))

                if bandwidth_values:
                    avg_bw = sum(bandwidth_values) / len(bandwidth_values)
                    # Assume Mbits/sec unit (most common)
                    results["average_bandwidth"] = f"{avg_bw:.2f} Mbits/sec"
                    results["average_bandwidth_numeric"] = avg_bw

                    # Check bandwidth threshold (75 Mbits/sec)
                    if avg_bw < 75:
                        results["bandwidth_warning"] = True

            results["parse_success"] = True

        except Exception as e:
            self.logger.warning(f"Failed to parse iperf3 output: {e}")
            results["parse_success"] = False

        return results

    def stop_iperf3_server(self) -> Dict[str, Any]:
        """
        Stop iperf3 server on edge1.

        Returns:
            Dictionary containing cleanup results
        """
        self.logger.info("Stopping iperf3 server on edge1...")

        try:
            stop_cmd = (
                "tmux kill-session -t iperf3_server 2>/dev/null || true; "
                "sudo pkill -f 'iperf3 -s' 2>/dev/null || true"
            )
            result = self.host_manager.execute_on_host(
                host_name="edge1", command=stop_cmd, background=False
            )
            result["success"] = True
            self.logger.info("✓ iperf3 server stopped successfully")
            return result

        except Exception as e:
            self.logger.error(f"Exception during iperf3 server cleanup: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_iperf3_processes(self) -> Dict[str, Any]:
        """
        Clean up any remaining iperf3 processes on both hosts.

        Returns:
            Dictionary containing cleanup results
        """
        self.logger.info("Cleaning up iperf3 processes...")

        cleanup_results = {
            "edge1": None,
            "amari": None,
            "overall_success": True,
        }

        # Cleanup on edge1
        try:
            edge1_cmd = (
                "tmux kill-session -t iperf3_server 2>/dev/null || true; "
                "sudo pkill -f 'iperf3' 2>/dev/null || true"
            )
            edge1_result = self.host_manager.execute_on_host(
                host_name="edge1", command=edge1_cmd, background=False
            )
            edge1_result["success"] = True
            cleanup_results["edge1"] = edge1_result
            self.logger.info("✓ edge1 iperf3 processes cleaned up")

        except Exception as e:
            self.logger.error(f"Error cleaning up edge1: {e}")
            cleanup_results["edge1"] = {"success": False, "error": str(e)}
            cleanup_results["overall_success"] = False

        # Cleanup on amari
        try:
            amari_cmd = "sudo pkill -f 'iperf3' 2>/dev/null || true"
            amari_result = self.host_manager.execute_on_host(
                host_name="amari", command=amari_cmd, background=False
            )
            amari_result["success"] = True
            cleanup_results["amari"] = amari_result
            self.logger.info("✓ amari iperf3 processes cleaned up")

        except Exception as e:
            self.logger.error(f"Error cleaning up amari: {e}")
            cleanup_results["amari"] = {"success": False, "error": str(e)}
            cleanup_results["overall_success"] = False

        return cleanup_results

    def test_connections(self) -> bool:
        """
        Test connections to required hosts.

        Returns:
            True if all connections successful, False otherwise
        """
        self.logger.info("Testing host connections...")

        connection_status = self.host_manager.test_connections()

        for host, status in connection_status.items():
            status_symbol = "✓" if status else "✗"
            self.logger.info(f"  {host}: {status_symbol}")

        required_hosts = ["edge1", "amari"]
        missing_hosts = [
            host
            for host in required_hosts
            if not connection_status.get(host, False)
        ]

        if missing_hosts:
            self.logger.error(
                f"Missing connections to required hosts: {missing_hosts}"
            )
            return False

        self.logger.info("✓ All required hosts are accessible")
        return True

    def display_results(self, results: Dict[str, Any]):
        """
        Display formatted throughput test results.

        Args:
            results: Parsed iperf3 results
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("THROUGHPUT TEST RESULTS")
        self.logger.info("=" * 60)

        if results["parse_success"]:
            if results["final_bandwidth"]:
                self.logger.info(
                    f"Final Bandwidth: {results['final_bandwidth']}"
                )

            if results["average_bandwidth"]:
                # Check for bandwidth warning
                if results.get("bandwidth_warning", False):
                    self.logger.warning(
                        "⚠️  AVERAGE BANDWIDTH WARNING:"
                        f" {results['average_bandwidth']} (Below threshold of"
                        " 75 Mbits/sec)"
                    )
                    self.logger.warning(
                        "🚨 Network performance may be degraded. Please check:"
                    )
                    self.logger.warning("   - Network connectivity")
                    self.logger.warning("   - UE namespace configuration")
                    self.logger.warning("   - Edge server status")
                    self.logger.warning("   - System resources")
                else:
                    self.logger.info(
                        f"✓ Average Bandwidth: {results['average_bandwidth']} "
                        "(Above threshold of 75 Mbits/sec)"
                    )

            if results["total_transferred"]:
                self.logger.info(
                    f"Total Transferred: {results['total_transferred']}"
                )

            if results["intervals"]:
                self.logger.info(f"Test Intervals: {len(results['intervals'])}")
                self.logger.info("\nInterval Details:")
                for i, interval in enumerate(results["intervals"], 1):
                    self.logger.info(
                        f"  {i:2d}."
                        f" {interval['start_time']:5.1f}-{interval['end_time']:5.1f}s:"
                        f" {interval['transferred']:>10} @"
                        f" {interval['bandwidth']}"
                    )
        else:
            self.logger.warning("Failed to parse iperf3 results")
            if results["raw_output"]:
                self.logger.info("Raw output:")
                for line in results["raw_output"].split("\n"):
                    if line.strip():
                        self.logger.info(f"  {line}")

        self.logger.info("=" * 60)

    def run_throughput_test(
        self, ue_namespace: str = "ue1", duration: int = 10, interval: int = 2
    ) -> Dict[str, Any]:
        """
        Run complete throughput test.

        Args:
            ue_namespace: UE namespace to use for client
            duration: Test duration in seconds
            interval: Reporting interval in seconds

        Returns:
            Dictionary containing complete test results
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING THROUGHPUT TEST")
        self.logger.info("=" * 60)

        test_results = {
            "success": False,
            "server_start": None,
            "client_test": None,
            "parsed_results": None,
            "cleanup": None,
            "bandwidth_warning": False,  # Add bandwidth warning flag
        }

        # Test connections first
        if not self.test_connections():
            self.logger.error(
                "Connection test failed, aborting throughput test"
            )
            return test_results

        try:
            # Step 1: Start iperf3 server
            self.logger.info("\n=== STEP 1: Starting iperf3 Server ===")
            server_result = self.start_iperf3_server()
            test_results["server_start"] = server_result

            if not server_result["success"]:
                self.logger.error(
                    "Failed to start iperf3 server, aborting test"
                )
                return test_results

            # Wait for server to initialize
            self.logger.info("Waiting 3 seconds for server to initialize...")
            time.sleep(3)

            # Step 2: Run client test
            self.logger.info(
                f"\n=== STEP 2: Running Client Test ({ue_namespace}) ==="
            )
            client_result = self.run_iperf3_client(
                ue_namespace, duration, interval
            )
            test_results["client_test"] = client_result

            if client_result["success"]:
                # Step 3: Parse results
                self.logger.info("\n=== STEP 3: Parsing Results ===")
                parsed_results = self.parse_iperf3_results(
                    client_result.get("output", "")
                )
                test_results["parsed_results"] = parsed_results
                test_results["bandwidth_warning"] = parsed_results.get(
                    "bandwidth_warning", False
                )

                # Display results
                self.display_results(parsed_results)
                test_results["success"] = True

            else:
                self.logger.error("Client test failed")

        finally:
            # Step 4: Cleanup
            self.logger.info("\n=== STEP 4: Cleanup ===")
            cleanup_result = self.cleanup_iperf3_processes()
            test_results["cleanup"] = cleanup_result

            if cleanup_result["overall_success"]:
                self.logger.info("✓ Cleanup completed successfully")
            else:
                self.logger.warning("⚠ Cleanup completed with some issues")

        # Final status
        self.logger.info("\n" + "=" * 60)
        if test_results["success"]:
            if test_results.get("bandwidth_warning", False):
                self.logger.warning(
                    "THROUGHPUT TEST COMPLETED WITH BANDWIDTH WARNING"
                )
                self.logger.warning(
                    "⚠️  Average bandwidth is below 75 Mbits/sec threshold"
                )
            else:
                self.logger.info("THROUGHPUT TEST COMPLETED SUCCESSFULLY")
                self.logger.info(
                    "✓ Average bandwidth is above 75 Mbits/sec threshold"
                )
        else:
            self.logger.info("THROUGHPUT TEST FAILED")
        self.logger.info("=" * 60)

        return test_results


def print_usage():
    """Print usage information."""
    print("Throughput Test Script")
    print("=" * 30)
    print("Usage:")
    print("  python throughput_test.py")
    print("")
    print("This script will:")
    print("  1. Start iperf3 server on edge1")
    print("  2. Run iperf3 client test from ue1 namespace on amari")
    print("  3. Display throughput results")
    print("  4. Clean up all iperf3 processes")


def main():
    """Main function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Create throughput test instance
    throughput_test = ThroughputTest()

    # Run the test
    start_time = time.time()
    results = throughput_test.run_throughput_test()
    end_time = time.time()

    # Print summary
    duration = end_time - start_time
    logger.info(f"\nTest Duration: {duration:.2f} seconds")

    if results["success"]:
        if results.get("bandwidth_warning", False):
            logger.warning(
                f"Result: SUCCESS WITH WARNING (Bandwidth below 75 Mbits/sec)"
            )
            # Exit with warning code (2) for bandwidth issues
            sys.exit(2)
        else:
            logger.info(f"Result: SUCCESS (Bandwidth above 75 Mbits/sec)")
            sys.exit(0)
    else:
        logger.error(f"Result: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
