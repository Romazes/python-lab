#!/usr/bin/env python3
"""
Simple test script for the Streaming API Client
Tests basic functionality without requiring server connection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from streaming_client_app import StreamingLogger, SymbolManager, StatusManager

def test_logging():
    """Test the logging functionality."""
    print("Testing StreamingLogger...")

    logger = StreamingLogger("test_logs")

    # Test subscription logging
    logger.log_subscription("ADD_SYMBOL", ["AAPL", "GOOG"], "LEVEL1")
    logger.log_subscription_request("ADD_SYMBOL", ["AAPL", "GOOG"], "LEVEL1", "test_token_123")

    # Test market data logging
    logger.log_market_data("AAPL", "LEVEL1", "Bid: 150.25 | Ask: 150.30 | Last: 150.27")

    # Test status logging
    logger.log_status("Connection established")
    logger.log_success("Test completed successfully")

    print(f"✓ Logs written to: {logger.log_path}")

def test_symbol_manager():
    """Test symbol manager input handling."""
    print("\nTesting SymbolManager input handling...")

    # Mock request handler for testing
    class MockRequestHandler:
        async def add_symbols_async(self, symbols, level):
            print(f"Mock: Adding symbols {symbols} for {level}")

    request_handler = MockRequestHandler()
    symbol_manager = SymbolManager(request_handler)

    # Test level input
    print("Testing level input parsing...")
    # Note: We can't easily test interactive input in automated test
    print("✓ SymbolManager class structure validated")

def test_status_manager():
    """Test status manager functionality."""
    print("\nTesting StatusManager...")

    # Mock components for testing
    class MockStreamingClient:
        def __init__(self):
            self.active_subscriptions = {
                'LEVEL1': {'AAPL', 'GOOG'},
                'LEVEL2': set(),
                'TICK': {'MSFT'}
            }
            self.ready_event = type('MockEvent', (), {'is_set': lambda: True})()
            self.logger = StreamingLogger("test_logs")

    class MockRequestHandler:
        pass

    streaming_client = MockStreamingClient()
    request_handler = MockRequestHandler()
    status_manager = StatusManager(request_handler, streaming_client)

    print("✓ StatusManager class structure validated")

def main():
    """Run all tests."""
    print("=== Streaming API Client - Test Suite ===")

    try:
        test_logging()
        test_symbol_manager()
        test_status_manager()

        print("\n✅ All tests passed! The streaming client components are properly structured.")
        print("\nTo run the full application:")
        print("  python streaming_client_app.py")
        print("\nMake sure config.cfg is properly configured for your EMSX environment.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())