# Streaming API Client (Python)

This directory contains a Python implementation of the Streaming Market Data Client that mirrors the functionality of the C# StreamingClientApp.

## Overview

The `streaming_client_app.py` script provides a command-line interface for bidirectional streaming market data operations with the EMS XAPI. It supports:

- **Adding symbols** to streaming subscriptions
- **Removing symbols** from streaming subscriptions
- **Changing subscription levels** (LEVEL1, LEVEL2, TICK)
- **Status monitoring** and connection health checks
- **Comprehensive logging** of all operations and market data

## Features

### Modular Architecture
- `StreamingClient`: Core streaming functionality and bidirectional communication
- `RequestHandler`: Manages subscription requests to the server
- `SymbolManager`: Handles user input for symbol operations
- `StatusManager`: Provides status monitoring and display
- `StreamingLogger`: Comprehensive logging system

### Enhanced Logging
- **Subscription Operations**: Logs all ADD_SYMBOL, REMOVE_SYMBOL, and CHANGE_SUBSCRIPTION operations
- **Request Details**: Captures complete request information including user tokens
- **Market Data**: Structured logging of all received market data
- **Status Updates**: Connection status and server acknowledgments
- **Error Handling**: Comprehensive error logging with context

### Bidirectional Streaming
- Single persistent connection for all operations
- Real-time market data streaming
- Dynamic subscription management without reconnection

## Prerequisites

1. **Python 3.8+**
2. **EMSX API Library**: Ensure `emsxapilibrary.py` and related files are in the parent `scripts` directory
3. **Protocol Buffers**: Generated Python files (`market_data_pb2.py`, `market_data_pb2_grpc.py`, etc.)
4. **Configuration**: `config.cfg` file with server connection details

## Installation

1. **Ensure Parent Configuration Exists**: Verify that `../config.cfg` exists in the parent `scripts` directory with proper EMSX API configuration.

2. **Install Dependencies**: Run the launcher script which will automatically install required Python packages:
   ```bash
   python run_streaming_client.py
   ```

3. **Configure EMSX API**: Update `../config.cfg` with your EMSX API credentials and server details.

4. **Run the Application**: Execute the launcher script to start the streaming client:
   ```bash
   python run_streaming_client.py
   ```

## Usage

### Running the Application

```bash
cd streaming-api-client
python streaming_client_app.py
```

### Command Menu

After successful login and connection, you'll see:

```
=== Streaming Market Data Client ===
Available commands:
1. Add symbols to stream
2. Remove symbols from stream
3. Change subscription level
4. Check status
5. Exit
==================================
```

### Example Usage

1. **Add Symbols**:
   ```
   Enter your choice (1-5): 1
   Enter symbols to add (comma-separated): AAPL, GOOG, MSFT
   Select level (1-3): 1
   Added AAPL, GOOG, MSFT for LEVEL1 data.
   ```

2. **Check Status**:
   ```
   Enter your choice (1-5): 4

   === Current Streaming Status ===
   Active Subscriptions:
     LEVEL1: AAPL, GOOG, MSFT
     LEVEL2: None
     TICK: None
   Connection Status: Connected
   Log File: logs/streaming_client_2025-12-01_19-30-15.log
   ================================
   ```

3. **Change Subscription Level**:
   ```
   Enter your choice (1-5): 3
   Enter symbols to change (comma-separated): AAPL
   Select level (1-3): 2
   Changed subscription for AAPL to LEVEL2.
   ```

## Log Files

The application creates timestamped log files in the `logs` directory:

```
logs/
└── streaming_client_2025-12-01_19-30-15.log
```

### Log Format Examples

```
2025-12-01 19:30:15 - StreamingClient - INFO - SUBSCRIPTION | ADD_SYMBOL | Symbols: [AAPL, GOOG] | Level: LEVEL1
2025-12-01 19:30:15 - StreamingClient - INFO - REQUEST | ADD_SYMBOL | Symbols: [AAPL, GOOG] | Level: LEVEL1 | Token: abc12345...
2025-12-01 19:30:16 - StreamingClient - INFO - MARKET_DATA | AAPL | LEVEL1 | Bid: 277.25 | Ask: 277.48 | Last: 0.00
2025-12-01 19:30:20 - StreamingClient - INFO - STATUS | Status check performed by user
```

## Configuration

The script uses the existing `config.cfg` file from the parent `scripts` directory. This ensures consistency with all other EMSX API scripts and avoids configuration duplication.

The configuration must be in the `[Auth Config Section]` format as used by all EMSX API scripts:

```ini
[Auth Config Section]
password = your-password
server = your-emsx-server-host.com
user = your-username
domain = your-domain
locale = your-locale
port = 9000
cert_file_path = roots_qa.pem
ssl = true
srp_login = false
keep_alive_time = 3600000
keep_alive_timeout = 30000
max_retry_count = 3
retry_delay_ms = 1000
```

### Required Configuration Fields:

- **password**: Your EMSX API password
- **server**: EMSX API server hostname
- **user**: Your EMSX API username
- **domain**: Authentication domain
- **locale**: Environment locale
- **port**: Server port (default: 9000)
- **cert_file_path**: Path to SSL certificate file
- **ssl**: Enable SSL connection (true/false)
- **srp_login**: Use SRP authentication (true/false)

The launcher script will verify that `../config.cfg` exists before running the application.

The script includes comprehensive error handling for:
- Connection failures
- Authentication errors
- Invalid user input
- Server response errors
- Streaming interruptions

All errors are logged to both console and log files with detailed context.

## Comparison with C# Version

This Python implementation mirrors the C# `StreamingClientApp` with:

| Feature | Python Version | C# Version |
|---------|----------------|------------|
| Modular Architecture | ✅ Classes: StreamingClient, RequestHandler, etc. | ✅ Classes: StreamingClient, RequestHandler, etc. |
| Subscription Logging | ✅ Detailed logging of all operations | ✅ Detailed logging of all operations |
| Bidirectional Streaming | ✅ Single persistent connection | ✅ Single persistent connection |
| Command Interface | ✅ Interactive menu system | ✅ Interactive menu system |
| Error Handling | ✅ Comprehensive exception handling | ✅ Comprehensive exception handling |
| Market Data Processing | ✅ LEVEL1, LEVEL2, TICK support | ✅ LEVEL1, LEVEL2, TICK support |

## Dependencies

- `emsxapilibrary.py` - EMSX API library
- `market_data_pb2.py` - Protocol buffer definitions
- `market_data_pb2_grpc.py` - gRPC service definitions
- `utilities_pb2.py` - Utility protocol buffers
- `utilities_pb2_grpc.py` - Utility gRPC services

## Troubleshooting

### Common Issues

1. **Login Failed**: Check `config.cfg` credentials and server settings
2. **Connection Timeout**: Verify server host/port and network connectivity
3. **Import Errors**: Ensure all required Python files are in the correct locations
4. **Permission Errors**: Check write permissions for log directory

### Log Analysis

Check the log files for detailed error information:
- Connection attempts and failures
- Server responses and acknowledgments
- Subscription operation results
- Market data processing errors

## Development Notes

This script was created to provide feature parity with the C# StreamingClientApp while leveraging the existing Python EMSX API infrastructure. It demonstrates:

- Proper async/await patterns in Python
- Thread-safe logging and console output
- Modular design principles
- Comprehensive error handling
- Structured logging for debugging and monitoring