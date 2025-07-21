# Remote Command Executor with YAML Configuration

This module uses the Fabric library to connect to remote hosts and execute commands in the background, with support for YAML configuration files to manage multiple hosts.

## Features

- Connect to remote hosts and execute background commands
- Support for SSH key and password authentication
- Support for proxy connections (ProxyCommand)
- YAML configuration file management for multiple hosts
- Automatic PID retrieval for background processes
- Support for command output redirection to log files
- Check background process status
- Batch command execution on multiple hosts
- Complete error handling and logging

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

### YAML Configuration File Structure

Create a `hosts_config.yaml` file to configure your hosts:

```yaml
hosts:
  amari:
    host: 192.168.0.15
    user: root
    port: 22
    key_filename: ~/.ssh/id_rsa
    proxy_command: ssh zx@dex.csres.utexas.edu -W 192.168.0.15:%p
    forward_agent: true
    timeout: 30
    description: "Amari host via proxy"
    
  edge0:
    host: edge0
    user: zx
    port: 22
    key_filename: ~/.ssh/id_rsa
    proxy_command: ssh zx@dex.csres.utexas.edu -W %h:%p
    forward_agent: false
    timeout: 30
    description: "Edge0 host via proxy"
    
  edge1:
    host: edge1
    user: zx
    port: 22
    key_filename: ~/.ssh/id_rsa
    proxy_command: ssh zx@dex.csres.utexas.edu -W %h:%p
    forward_agent: false
    timeout: 30
    description: "Edge1 host via proxy"

defaults:
  timeout: 30
  port: 22
  key_filename: ~/.ssh/id_rsa
  forward_agent: false

proxy:
  host: dex.csres.utexas.edu
  user: zx
  port: 22
  key_filename: ~/.ssh/id_rsa
```

## Usage

### Basic Usage

```python
from src.host_manager import HostManager

# Create host manager
manager = HostManager("hosts_config.yaml")

# List all available hosts
hosts = manager.list_hosts()
print(hosts)

# Execute command on specific host
result = manager.execute_on_host(
    host_name="amari",
    command="echo 'Hello from amari' && hostname"
)

print(f"Success: {result['success']}")
print(f"PID: {result['pid']}")
print(f"Output: {result['output']}")
```

### Batch Execution

```python
# Execute command on all hosts
all_results = manager.execute_on_all_hosts(
    command="echo 'Broadcast message' && date"
)

for host, result in all_results.items():
    print(f"{host}: {result['success']}")
```

### Connection Testing

```python
# Test connections to all hosts
connection_status = manager.test_connections()
for host, status in connection_status.items():
    print(f"{host}: {'✓' if status else '✗'}")
```

### Convenience Functions

```python
from src.host_manager import execute_on_host

# Execute command directly
result = execute_on_host(
    host_name="edge0",
    command="uptime"
)
```

## Advanced Features

### Background Task Execution

```python
# Execute long-running task
result = manager.execute_on_host(
    host_name="amari",
    command="python3 /path/to/long_running_script.py"
)

if result['success'] and result['pid']:
    print(f"Task started with PID: {result['pid']}")
```

### Command Execution with Logging

```python
from src.remote_executor import execute_background_command_with_logging

# Redirect output to log file
result = execute_background_command_with_logging(
    host="192.168.0.15",
    command="python3 /path/to/script.py",
    log_file="/tmp/script.log",
    user="root",
    key_filename="~/.ssh/id_rsa"
)
```

### Basic Environment Setup

```python
from src.basic_env_setup import BasicEnvSetup

# Create setup instance
setup = BasicEnvSetup()

# Set up complete environment (LTE + 5G)
results = setup.setup_complete_environment(wait_time=15)

# Check if setup was successful
if results['overall_success']:
    print("Environment setup completed successfully!")
else:
    print("Setup completed with errors")

# Clean up environment when done
cleanup_results = setup.cleanup_environment()
```

## Configuration Parameters

### Host Configuration Parameters

- `host`: Remote host IP address or hostname
- `user`: SSH username
- `port`: SSH port (default: 22)
- `key_filename`: SSH private key file path
- `proxy_command`: SSH proxy command
- `forward_agent`: Whether to forward SSH agent
- `timeout`: Connection timeout in seconds
- `description`: Host description

### Default Configuration

The `defaults` section defines default values for all hosts. If a host doesn't specify a parameter, the default value will be used.

### Proxy Configuration

The `proxy` section defines proxy server configuration information.

## Return Value Format

All execution functions return a dictionary containing the following keys:

- `success`: Boolean indicating if command was executed successfully
- `pid`: Background process PID (if available)
- `output`: Immediate command output
- `error`: Error message if execution failed
- `connection_info`: Connection information

## Error Handling

The module includes complete error handling mechanisms:

- Configuration file loading failures are logged
- Connection failures return detailed error information
- Command execution failures are logged
- All exceptions are caught and logged

## Security Considerations

1. Prefer SSH key authentication over passwords
2. Ensure SSH private key file permissions are correct (600)
3. Don't hardcode passwords in code
4. Use environment variables or configuration files for sensitive information
5. Regularly update SSH keys

## Logging

The module uses Python's logging module to record operation information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Example Files

- `hosts_config.yaml`: Host configuration file example
- `src/basic_env_setup.py`: Basic environment setup for LTE and 5G services
- `src/example_basic_setup.py`: Example usage of the basic environment setup

## Troubleshooting

### Common Issues

1. **Connection failures**: Check SSH key permissions and network connectivity
2. **Proxy connection issues**: Ensure proxy server is accessible
3. **Permission errors**: Check user permissions and file permissions
4. **Timeout errors**: Increase timeout parameter value

### Debug Mode

Enable detailed logging to debug issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
``` 