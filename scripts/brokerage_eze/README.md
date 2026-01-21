# Python XAPI Client

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![gRPC](https://img.shields.io/badge/gRPC-Latest-green.svg)](https://grpc.io/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#license)

The Python XAPI client provides a comprehensive interface for interacting with the Eze EMS XAPI server, supporting both market data streaming and trading operations through gRPC.

## Features

- **Interactive Streaming Client**: Command-line application for bidirectional streaming with menu-driven interface (December 2025)
- **Bidirectional Streaming**: Real-time market data streaming with dynamic subscription management
- **Modular Architecture**: Separate concerns with StreamingClient, RequestHandler, StatusManager, and SymbolManager classes
- **Enhanced Logging**: Comprehensive file-based logging where market data responses are logged (not printed to console)
- **Order Management**: Complete trading API for order submission, modification, and cancellation
- **Market Data**: Level 1/2 quotes, historical bars, tick data, and options chains
- **Authentication**: Secure token-based authentication with SRP protocol
- **Error Handling**: Comprehensive exception handling and connection management
- **Validation Tools**: Dedicated scripts for API validation and testing

## Installation

1. Ensure Python 3.8+ is installed
2. Install required dependencies:
```bash
pip install grpcio grpcio-tools protobuf
```

3. Configure the client:
   - Copy `config.cfg` and update server endpoints
   - Ensure SSL certificates are properly configured

## Quick Start

```python
from emsxapilibrary import EMSXAPILibrary

# Initialize and authenticate
api = EMSXAPILibrary()
api.login()

# Example: Get user accounts
accounts = api.get_user_accounts()
print(accounts)
```

## Core Components

### EMSXAPILibrary
Main client library providing high-level API access:
- Authentication and session management
- Order operations (submit, modify, cancel)
- Market data requests
- Account and position queries

### Streaming Market Data Client (New - December 2025)
**Interactive command-line client mirroring C# StreamingClientApp functionality:**

**Architecture:**
- **StreamingClient**: Core bidirectional streaming with synchronous gRPC and asyncio
- **RequestHandler**: Manages ADD_SYMBOL, REMOVE_SYMBOL, CHANGE_SUBSCRIPTION requests
- **SymbolManager**: Handles user input for symbol operations
- **StatusManager**: Displays connection and subscription status
- **StreamingLogger**: File-based logging (INFO to files, WARNING to console)

**Features:**
- Modular architecture with comprehensive logging
- Dynamic symbol subscription management (add/remove/change)
- Multi-level market data support (Level1, Level2, Tick)
- Clean console interface - market data responses logged to files, not printed
- Thread-safe operations with threading.Lock and queue.Queue
- Proper error handling and graceful cleanup

**Location**: `scripts/streaming-api-client/`
**Main Script**: `streaming_client_app.py` (615 lines)
**Launcher**: `run_streaming_client.py` (dependency checker)
**Documentation**: Mirrors C# implementation in `Client/CSharp/StreamingClientApp/`

### Bidirectional Streaming
Real-time market data streaming with dynamic subscriptions:
- Level 1, Level 2, and Tick data
- Symbol addition/removal
- Subscription level changes
- Continuous data flow management

## Examples

### Interactive Streaming Client (Recommended)
```bash
# Launch with dependency checking
cd scripts/streaming-api-client
python run_streaming_client.py

# Or run directly
python streaming_client_app.py

# Interactive menu options:
# 1. Add symbols to stream (with level selection)
# 2. Remove symbols from stream
# 3. Change subscription level
# 4. Check status (shows active subscriptions)
# 5. Exit

# All market data responses are logged to:
# logs/streaming_client_YYYY-MM-DD_HH-MM-SS.log
```

**Sample Workflow:**
```python
# After login, the client presents an interactive menu:
=== Streaming Market Data Client ===
Available commands:
1. Add symbols to stream
2. Remove symbols from stream
3. Change subscription level
4. Check status
5. Exit

# Example: Add AAPL for Level1 data
Enter your choice (1-5): 1
Enter symbols to add (comma-separated): AAPL
Select level (1-3): 1  # LEVEL1

# Market data responses are logged to file
# Console shows only warnings/errors for clean UX
```

### Basic Market Data Streaming
```python
# See Examples/ directory for complete examples
from streamMarketDataBidirectional import StreamMarketDataBidirectional

streamer = StreamMarketDataBidirectional()
streamer.run()
```

### Order Submission
```python
# Submit a single order
order_details = {
    'symbol': 'AAPL',
    'quantity': 100,
    'price': 150.00,
    'side': 'BUY'
}
order_id = api.submit_single_order(order_details)
```

## Validation Scripts

### validate_change_subscription.py
**Comprehensive validation for CHANGE_SUBSCRIPTION functionality:**

- ? Validates all market data level transitions (LEVEL1↔LEVEL2, LEVEL1↔TICK, LEVEL2↔TICK)
- ? Tests error conditions (empty symbols, invalid levels, nonexistent symbols)
- ? Thread-safe request queuing with threading.Lock
- ? Detailed success/failure metrics and timing analysis
- ? Queue-based request management for concurrent operations

**Key Features:**
```python
# Validate level transitions
validator.validate_level_transition("AAPL", "LEVEL1", "LEVEL2")
validator.validate_level_transition("MSFT", "LEVEL2", "TICK")

# Test error conditions
validator.validate_error_condition("INVALID", "LEVEL1", "Symbol not found")
validator.validate_error_condition("", "LEVEL2", "Empty symbol list")
```

**Usage:**
```bash
python validate_change_subscription.py
```

**Validation Coverage:**
- **Level Transitions**: LEVEL1→LEVEL2, LEVEL2→LEVEL1, LEVEL1→TICK, TICK→LEVEL1, LEVEL2→TICK, TICK→LEVEL2
- **Error Conditions**: Empty symbol arrays, invalid market data levels, nonexistent symbols
- **Response Validation**: Success acknowledgements, error messages, data integrity checks
- **Performance Metrics**: Response times, success rates, failure analysis

## Supported Operations

### Market Data
- **Interactive Streaming Client**: Command-line client with menu-driven interface for StreamMarketData API
- **Stream Market Data**: Bidirectional streaming with dynamic subscriptions
- **Get Historical Bars**: Daily, weekly, monthly, and intraday bars
- **Get Level 1/2 Data**: Real-time quotes and market depth
- **Get Tick Data**: Individual trade ticks
- **Get Options Chain**: Complete options data for underliers

### Trading Operations
- **Submit Orders**: Single, basket, pair, and spread orders
- **Modify Orders**: Change price, quantity, or other parameters
- **Cancel Orders**: Individual and batch order cancellation
- **Order Status**: Real-time order tracking and execution reporting

### Account Management
- **Get User Accounts**: Available trading accounts
- **Get Positions**: Current positions and balances
- **Get Activity**: Today's trading activity and history

## Cross-Platform Implementation

### Python vs C# Streaming Clients

The Python streaming client mirrors the C# StreamingClientApp architecture:

| Component | Python | C# |
|-----------|--------|----|
| Core Streaming | `StreamingClient` class | `StreamingClient.cs` |
| Request Management | `RequestHandler` class | `RequestHandler.cs` |
| Symbol Operations | `SymbolManager` class | `SymbolManager.cs` |
| Status Display | `StatusManager` class | `StatusManager.cs` |
| Logging | `StreamingLogger` class | `StreamingLogger.cs` |
| Data Formatting | Python native | `DataFormatter.cs` |

**Key Differences:**
- **Python**: Uses synchronous gRPC with threading for bidirectional streaming
- **C#**: Uses async/await with Task-based asynchronous pattern
- **Python**: 615 lines in single file for simplicity
- **C#**: Modular project structure with separate files per component

**Shared Capabilities:**
- Bidirectional streaming with dynamic subscriptions
- File-based logging (responses logged, not printed)
- Interactive command-line interface
- Thread-safe operations
- Comprehensive error handling

## Configuration

### config.cfg
```ini
[DEFAULT]
server_url = your-server-url
ssl_cert_path = path/to/certificate.pem
timeout = 30
```

### Environment Variables
- `XAPI_CONFIG_PATH`: Path to configuration file
- `XAPI_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Error Handling

The client includes comprehensive error handling:

- `LoginFailedException`: Authentication failures
- `NetworkFailedException`: Connection issues
- `ServerNotAvailableException`: Server unreachable
- `SessionNotFoundException`: Invalid sessions
- `StreamingAlreadyExistsException`: Duplicate streams

## Best Practices

1. **Connection Management**: Always properly close connections
2. **Error Handling**: Implement try/catch blocks for all API calls
3. **Authentication**: Cache tokens and handle expiration
4. **Streaming**: Monitor stream health and implement reconnection logic
5. **Rate Limiting**: Respect API rate limits to avoid throttling

## Dependencies

- grpcio>=1.50.0
- grpcio-tools>=1.50.0
- protobuf>=4.21.0
- requests>=2.28.0

## Troubleshooting

### Common Issues
- **Authentication failures**: Verify credentials and server URL
- **Connection timeouts**: Check network connectivity and firewall settings
- **SSL certificate errors**: Ensure certificate path is correct and valid
- **Protobuf import errors**: Regenerate protobuf files if needed

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Running Tests
```bash
# Run validation scripts
python validate_change_subscription.py

# Run other examples
python Examples/submitsingleorder.py
```

### Contributing
- Follow PEP 8 style guidelines
- Add comprehensive error handling
- Include docstrings for all public methods
- Test all changes thoroughly

## Related Documentation

- [Main Project README](../../readme.md)
- [Server Documentation](../../Server/README_ServerCode.md)
- [C# Client Documentation](../CSharp/CSharp_XAPI_Client/Readme_CsharpClient.md)
- [C# Streaming Client](../CSharp/StreamingClientApp/README.md) - C# implementation with identical architecture
- [C# StreamingClient.cs](../CSharp/StreamingClientApp/Core/StreamingClient.cs) - Core streaming implementation
- [Server Unit Tests](../../Server/XAPIServer.UnitTests/README.md) - Bidirectional streaming test coverage
- [Administrative Tools](../../AdminClientScripts/README_Admin_Client.md)
- [Bidirectional Streaming API Documentation](../../docs/Bidirectional-Market-Data-Streaming-API-Documentation.md)</content>
<parameter name="filePath">c:\_EMS\GitLab\TOOL-cross-platform-api\Client\XapiClient\README.md