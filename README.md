# SMEC Automated Evaluation

## Overview

This repository contains the automated evaluation scripts for reproducing the experimental results and figures presented in the paper titled "Enabling SLO-Aware 5G Multi-Access Edge Computing with SMEC," accepted at NSDI 2026.
The scripts automatically configure and run the system components and example applications found in the repositories in the [GitHub project organization page](https://github.com/smec-project).

### About SMEC

SLO-Aware Multi-Access Edge Computing (SMEC) is a resource management framework that incorporates SLO awareness into multi-access edge computing environments.
SMEC aims to maximize SLO satisfaction rates for latency-critical applications by reducing tail latency and improving performance predictability. 

## Prerequisites

**Important Note**: All configurations and scripts in this repository are tested on the **UTNS (University of Texas Network Systems) testbed**. 
The testbed infrastructure, network topology, and hardware specifications are integral to reproducing the paper's results.

Before running the evaluation scripts, ensure you have:

- Python 3.8 or higher
- SSH access to UTNS testbed nodes

Install required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

### Step 1: Configure SSH Connection

Before running any experiments, you need to configure the SSH connection settings in `hosts_config.yaml`.

#### File Location

```text
auto-evaluation/hosts_config.yaml
```

#### Required Changes

The repository already includes a working `hosts_config.yaml` for the UTNS testbed. In most cases, you can keep it as-is and only update the SSH private key path (`key_filename`) to match your local key.

Below is an example configuration consistent with the current `hosts_config.yaml` in this repo (you typically only need to change `key_filename`):

```yaml
hosts:
  amari:
    host: 192.168.0.15
    user: root
    port: 22
    key_filename: ~/.ssh/id_rsa    # Change this to your local SSH private key path
    proxy_command: ssh zx@dex.csres.utexas.edu -W 192.168.0.15:%p

  ran_server:
    host: edge0
    user: zx
    port: 22
    key_filename: ~/.ssh/id_rsa    # Change this to your local SSH private key path
    proxy_command: ssh zx@dex.csres.utexas.edu -W %h:%p

  edge_server:
    host: ipu0
    user: zx
    port: 22
    key_filename: ~/.ssh/id_rsa    # Change this to your local SSH private key path
    proxy_command: ssh zx@dex.csres.utexas.edu -W %h:%p

proxy:
  host: dex.csres.utexas.edu
  user: zx
  port: 22
  key_filename: ~/.ssh/id_rsa      # Change this to your local SSH private key path
```

#### For UTNS Testbed Users

If you are using the UTNS testbed for artifact evaluation (pre-configured environment):

1. **Public Key Setup**: The authors will help configure your public SSH key on the UTNS testbed nodes.
2. **Key Path Update (Required)**: You only need to update **`key_filename`** in `hosts_config.yaml` to point to your **local private key** that matches the configured public key.

Example:

```yaml
key_filename: /home/yourname/.ssh/id_rsa_utns
```

### Step 2: Verify Configuration

Test your SSH connections before running experiments:

```bash
python3 auto_evaluation.py -m test
```

This will verify that all configured hosts are reachable.

## Running the Evaluation

The evaluation process consists of three main steps, executed using the `auto_evaluation.py` script:

### Step 1: Data Collection (Mode: `data`)

This step runs all experiments and collects raw data from the testbed.

```bash
python auto_evaluation.py -m data
```

**Expected Duration**: Approximately **3 hours**

**What it does**:

- Deploys SMEC and baseline schedulers on the testbed
- Runs experiments with different workload configurations (static and dynamic)
- Runs experiments with different scheduler configurations (SMEC, ARMA, Tutti, Default)
- Collects raw logs from all testbed nodes (RAN logs, scheduler logs, server results, client results)
- Stores all collected data in the `results/` directory

**Output Directory Structure**:

```text
results/
├── arma_all_tasks/
├── arma_all_tasks_dynamic/
├── default_all_tasks/
├── default_all_tasks_dynamic/
├── smec_all_tasks/
├── smec_all_tasks_disable/
├── smec_all_tasks_disable_32cpu/
├── smec_all_tasks_dynamic/
├── smec_all_tasks_dynamic_disable/
├── smec_all_tasks_dynamic_disable_32cpu/
├── smec_all_tasks_dynamic_rtt/
├── smec_all_tasks_dynamic_wo_drop/
├── smec_all_tasks_rtt/
├── smec_all_tasks_wo_drop/
├── tutti_all_tasks/
└── tutti_all_tasks_dynamic/
```

### Step 2: Data Preprocessing (Mode: `preprocess`)

This step processes raw logs and extracts relevant metrics for figure generation.

```bash
python auto_evaluation.py -m preprocess
```

**Expected Duration**: Less than **5 minutes**

**What it does**:

- **Part 1**: Processes controller logs to extract remaining time information
  - Processes `smec_all_tasks/controller.log`
  - Processes `smec_all_tasks_dynamic/controller.log`
  - Generates `remaining_time_ue*.txt` files in respective server directories

- **Part 2**: Processes scheduler logs to extract waiting and processing time information
  - Processes `smec_all_tasks_disable_32cpu/scheduler.log`
  - Processes `smec_all_tasks_dynamic_disable_32cpu/scheduler.log`
  - Generates `waiting_client*.txt` and `processing_client*.txt` files in respective server directories

**Output Files** (added to results directories):

```text
results/
├── smec_all_tasks/
│   ├── video-transcoding/server/remaining_time_ue1.txt
│   ├── video-transcoding/server/remaining_time_ue2.txt
│   ├── video-od/server/remaining_time_ue3.txt
│   └── ...
├── smec_all_tasks_disable_32cpu/
│   ├── video-transcoding/server/waiting_client001.txt
│   ├── video-transcoding/server/processing_client0001.txt
│   └── ...
```

### Step 3: Evaluation Figure Generation (Mode: `figures`)

This step generates all evaluation figures presented in the paper.

```bash
python auto_evaluation.py -m figures
```

**Expected Duration**: Less than **2 minutes**

**What it does**:

- Reads processed data from `results/` directory
- Generates all paper evaluation figures (Figure 9 through Figure 21)
- Saves figures in PDF format to the `figures/` directory

**Generated Evaluation Figures**:

```text
figures/
├── figure_9.pdf      # Static workload - End-to-end latency (SMEC vs baselines)
├── figure_10.pdf     # Static workload - Throughput comparison
├── figure_11.pdf     # Static workload - SLO violation rate
├── figure_12.pdf     # Static workload - Resource utilization
├── figure_13.pdf     # Dynamic workload - End-to-end latency
├── figure_14.pdf     # Dynamic workload - Throughput comparison
├── figure_15.pdf     # Dynamic workload - SLO violation rate
├── figure_16.pdf     # Dynamic workload - Resource utilization
├── figure_17.pdf     # Best-effort task throughput
├── figure_18_a.pdf   # Microbenchmark - Processing time estimation
├── figure_18_b.pdf   # Microbenchmark - Queue waiting time estimation
├── figure_19.pdf     # Remaining time estimation error (P99)
├── figure_20_a.pdf   # Network latency estimation error (Box plot)
├── figure_20_b.pdf   # Processing time estimation error (Box plot)
└── figure_21.pdf     # Scheduler overhead analysis
```

### Optional: Measurement Figure Generation (Mode: `measurement`)

This optional step generates measurement-related figures based on pre-collected data from real-world 5G deployments.

```bash
python auto_evaluation.py -m measurement
```

**Expected Duration**: Less than **1 minutes**

**What it does**:

- Reads pre-collected measurement data from `measurements/` directory
- Generates latency decomposition, E2E latency CDF, and compute contention figures
- Saves figures in PDF format to the `figures/` directory

**Generated Measurement Figures**:

```text
figures/
├── figure_1.pdf      # E2E Latency CDF (SS)
├── figure_2.pdf      # Latency Decomposition (City-1)
├── figure_4.pdf      # Compute Contention CDF (SS - City-1)
├── figure_22.pdf     # E2E Latency CDF (AR)
├── figure_23.pdf     # Compute Contention CDF (SS - City-2)
├── figure_24.pdf     # Compute Contention CDF (SS - City-3)
├── figure_25.pdf     # Compute Contention CDF (AR - City-1)
├── figure_26.pdf     # Compute Contention CDF (AR - City-2)
├── figure_27.pdf     # Compute Contention CDF (AR - City-3)
├── figure_28a.pdf    # Latency Decomposition (City-2)
└── figure_28b.pdf    # Latency Decomposition (City-3)
```

## Complete Workflow Example

To reproduce all experiments and figures from scratch:

```bash
# Step 1: Collect experimental data (~3 hours)
python auto_evaluation.py -m data

# Step 2: Preprocess the collected data (~5 minutes)
python auto_evaluation.py -m preprocess

# Step 3: Generate evaluation figures (~2 minutes)
python auto_evaluation.py -m figures

# Optional: Generate measurement figures (~1 minute)
python auto_evaluation.py -m measurement
```

**Total Time**: Approximately **3 hours and 10 minutes**

## Output Directories

After running all three steps, you will have:

1. **`results/`**: Contains all raw and processed experimental data
   - Raw logs from testbed nodes
   - Processed metrics files
   - Intermediate data files

2. **`figures/`**: Contains all generated figures in PDF format
   - Evaluation figures (Figures 9-21)
   - Optional: Measurement figures (Figures 1, 2, 4, 22-28)
