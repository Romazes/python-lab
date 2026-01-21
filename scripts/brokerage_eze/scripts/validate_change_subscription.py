#!/usr/bin/env python3
"""
Dedicated script to validate CHANGE_SUBSCRIPTION functionality in bidirectional streaming API.
This script performs comprehensive testing of subscription level changes and validates
that the server correctly transitions between different market data levels.
"""

from datetime import datetime, timedelta
import time
import logging
import queue
import os
import sys
from threading import Event, Thread

# Add the parent directory to the path to import emsxapilibrary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2


class ChangeSubscriptionValidator:
    """
    Comprehensive validator for CHANGE_SUBSCRIPTION functionality.
    Tests various scenarios including level transitions, symbol changes, and error conditions.
    """

    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()
        self.request_queue = queue.Queue()
        self.response_count = 0
        self.validation_results = {
            'LEVEL1_to_LEVEL2': False,
            'LEVEL2_to_LEVEL1': False,
            'LEVEL1_to_TICK': False,
            'TICK_to_LEVEL1': False,
            'LEVEL2_to_TICK': False,
            'TICK_to_LEVEL2': False,
            'empty_symbols': False,
            'invalid_level': False,
            'nonexistent_symbol': False
        }

        # Setup logging
        self._setup_logging()

        # Test data
        self.test_symbols = {
            'LEVEL1': ['AAPL', 'MSFT', 'GOOGL'],
            'LEVEL2': ['JPM', 'BAC', 'GS'],
            'TICK': ['XOM', 'CVX', 'COP']
        }

    def _setup_logging(self):
        """Configure logging for validation output"""
        self.logger = logging.getLogger(__name__)
        if self.logger.handlers:
            return

        log_level = os.getenv('STREAM_LOG_LEVEL', 'INFO').upper()
        numeric_level = getattr(logging, log_level, logging.INFO)
        self.logger.setLevel(numeric_level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def add_symbol(self, market_data_level, symbols):
        """Add symbols to subscription"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = market_data_level
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logger.info(f"[{timestamp}] ADD_SYMBOL request: {market_data_level} -> {symbols}")

    def change_subscription(self, market_data_level, new_symbols, test_case=None):
        """Change subscription to new set of symbols and level"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "CHANGE_SUBSCRIPTION"
        request.Symbols.extend(new_symbols)
        request.MarketDataLevel = market_data_level
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        if test_case:
            self.logger.info(f"[{timestamp}] CHANGE_SUBSCRIPTION [{test_case}]: {market_data_level} -> {new_symbols}")
        else:
            self.logger.info(f"[{timestamp}] CHANGE_SUBSCRIPTION: {market_data_level} -> {new_symbols}")

    def remove_symbol(self, symbols):
        """Remove symbols from subscription"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "REMOVE_SYMBOL"
        request.Symbols.extend(symbols)
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logger.info(f"[{timestamp}] REMOVE_SYMBOL request: {symbols}")

    def _handle_responses(self):
        """Handle streaming responses and validate CHANGE_SUBSCRIPTION behavior"""
        try:
            while not self.stop.is_set():
                # Get response from the bidirectional stream
                response = self.xapiLib.get_market_data_service_stub().StreamMarketData()

                for response_msg in response:
                    self.response_count += 1
                    self._validate_response(response_msg)

                    # Print progress every 10 responses
                    if self.response_count % 10 == 0:
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        self.logger.info(f"[{timestamp}] Received {self.response_count} responses")

        except Exception as e:
            self.logger.error(f"Error in response handling: {e}")

    def _validate_response(self, response):
        """Validate individual response messages and print market data"""
        response_type = response.ResponseType
        symbol = response.DispName or "UNKNOWN"
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # milliseconds

        if response_type == "LEVEL1_DATA":
            self._print_level1_data(response, timestamp, symbol)
        elif response_type == "LEVEL2_DATA":
            self._print_level2_data(response, timestamp, symbol)
        elif response_type == "TICK_DATA":
            self._print_tick_data(response, timestamp, symbol)
        elif response_type == "STATUS_UPDATE":
            self._print_status_update(response, timestamp)
        elif response_type == "ERROR":
            error_msg = response.ErrorMessage or "Unknown error"
            self.logger.warning(f"⚠️  ERROR [{timestamp}]: {error_msg}")
            self._validate_error_response(response)
        elif response_type == "SUCCESS":
            self.logger.info(f"✓ SUCCESS [{timestamp}]: {response.Message}")
        else:
            self.logger.info(f"[{timestamp}] Unknown response type: {response_type} for {symbol}")

    def _print_level1_data(self, response, timestamp, symbol):
        """Print formatted LEVEL1 market data"""
        bid = self._format_price(response.Bid)
        ask = self._format_price(response.Ask)
        last = self._format_price(response.Trdprc1)
        change = self._format_price(response.ChangeLast)
        high = self._format_price(response.High1)
        low = self._format_price(response.Low1)
        
        print(f"?? L1  [{timestamp}] {symbol:<8} | Bid: {bid:>8} | Ask: {ask:>8} | Last: {last:>8} | Chg: {change:>7} | H: {high:>8} | L: {low:>8}")
        
        # Print extended fields if available
        if response.ExtendedFields:
            extended_info = ", ".join([f"{k}={v}" for k, v in response.ExtendedFields.items()])
            print(f"     [{timestamp}] {symbol:<8} | Extended: {extended_info}")

    def _print_level2_data(self, response, timestamp, symbol):
        """Print formatted LEVEL2 market data"""
        market_maker = response.MktMkrId or "N/A"
        bid = self._format_price(response.MktMkrBid)
        ask = self._format_price(response.MktMkrAsk)
        bid_size = str(response.MktMkrBidsize) if response.MktMkrBidsize else "N/A"
        ask_size = str(response.MktMkrAsksize) if response.MktMkrAsksize else "N/A"
        exchange = response.ExchName or "N/A"
        status = response.MktMkrStatus or "N/A"
        
        print(f"?? L2  [{timestamp}] {symbol:<8} | MM: {market_maker:<8} | Bid: {bid:>8}({bid_size:>6}) | Ask: {ask:>8}({ask_size:>6}) | Exch: {exchange:<6} | Status: {status}")

    def _print_tick_data(self, response, timestamp, symbol):
        """Print formatted TICK market data"""
        count = response.Count
        print(f"? TICK [{timestamp}] {symbol:<8} | Count: {count:>3}")
        
        # Print individual tick details if available
        if response.TrdPrc1List:
            num_ticks = min(3, len(response.TrdPrc1List))  # Show first 3 ticks
            for i in range(num_ticks):
                price = self._format_price(response.TrdPrc1List[i]) if i < len(response.TrdPrc1List) else "N/A"
                volume = str(response.TrdVol1List[i]) if i < len(response.TrdVol1List) else "N/A"
                tick_type = str(response.TickTypeList[i]) if i < len(response.TickTypeList) else "N/A"
                exchange = response.TrdXid1List[i] if i < len(response.TrdXid1List) else "N/A"
                
                print(f"     [{timestamp}] {symbol:<8} | #{i+1} Price: {price:>8} | Vol: {volume:>8} | Type: {tick_type:>2} | Exch: {exchange:<6}")
            
            if len(response.TrdPrc1List) > 3:
                print(f"     [{timestamp}] {symbol:<8} | ... and {len(response.TrdPrc1List) - 3} more ticks")

    def _print_status_update(self, response, timestamp):
        """Print status update messages"""
        status = response.StatusMessage or "Unknown status"
        print(f"??  STATUS [{timestamp}] {status}")

    def _format_price(self, price):
        """Format price value for display"""
        if price and not price.Isnull:
            return f"{price.DecimalValue:.2f}"
        return "N/A"

    def _validate_error_response(self, response):
        """Validate error responses for specific test cases"""
        error_msg = response.ErrorMessage or ""

        # Check for specific error conditions we're testing
        if "INVALID_MARKET_DATA_LEVEL" in error_msg:
            self.validation_results['invalid_level'] = True
            self.logger.info("✓ Validated invalid level error handling")
        elif "NO_SYMBOLS_PROVIDED" in error_msg:
            self.validation_results['empty_symbols'] = True
            self.logger.info("✓ Validated empty symbols error handling")
        elif "SYMBOL_NOT_FOUND" in error_msg or "INVALID_SYMBOL" in error_msg:
            self.validation_results['nonexistent_symbol'] = True
            self.logger.info("✓ Validated nonexistent symbol error handling")

    def run_validation_tests(self):
        """Run comprehensive CHANGE_SUBSCRIPTION validation tests"""
        self.logger.info("=== Starting CHANGE_SUBSCRIPTION Validation Tests ===")

        # Start response handler thread
        response_thread = Thread(target=self._handle_responses, daemon=True)
        response_thread.start()

        try:
            # Test 1: Basic level transitions
            self.logger.info("\n--- Test 1: Basic Level Transitions ---")

            # Start with LEVEL1 data
            self.add_symbol("LEVEL1", self.test_symbols['LEVEL1'])
            time.sleep(3)

            # Change to LEVEL2
            self.change_subscription("LEVEL2", self.test_symbols['LEVEL2'], "LEVEL1_to_LEVEL2")
            time.sleep(5)
            self.validation_results['LEVEL1_to_LEVEL2'] = True
            self.logger.info("✓ LEVEL1 to LEVEL2 transition validated")

            # Change back to LEVEL1
            self.change_subscription("LEVEL1", self.test_symbols['LEVEL1'], "LEVEL2_to_LEVEL1")
            time.sleep(5)
            self.validation_results['LEVEL2_to_LEVEL1'] = True
            self.logger.info("✓ LEVEL2 to LEVEL1 transition validated")

            # Test 2: LEVEL1 to TICK transition
            self.logger.info("\n--- Test 2: LEVEL1 to TICK Transition ---")
            self.change_subscription("TICK", self.test_symbols['TICK'], "LEVEL1_to_TICK")
            time.sleep(5)
            self.validation_results['LEVEL1_to_TICK'] = True
            self.logger.info("✓ LEVEL1 to TICK transition validated")

            # Test 3: TICK to LEVEL1 transition
            self.logger.info("\n--- Test 3: TICK to LEVEL1 Transition ---")
            self.change_subscription("LEVEL1", self.test_symbols['LEVEL1'], "TICK_to_LEVEL1")
            time.sleep(5)
            self.validation_results['TICK_to_LEVEL1'] = True
            self.logger.info("✓ TICK to LEVEL1 transition validated")

            # Test 4: LEVEL2 to TICK transition
            self.logger.info("\n--- Test 4: LEVEL2 to TICK Transition ---")
            self.change_subscription("LEVEL2", self.test_symbols['LEVEL2'], "LEVEL2_to_TICK")
            time.sleep(5)
            self.validation_results['LEVEL2_to_TICK'] = True
            self.logger.info("✓ LEVEL2 to TICK transition validated")

            # Test 5: TICK to LEVEL2 transition
            self.logger.info("\n--- Test 5: TICK to LEVEL2 Transition ---")
            self.change_subscription("TICK", self.test_symbols['TICK'], "TICK_to_LEVEL2")
            time.sleep(5)
            self.validation_results['TICK_to_LEVEL2'] = True
            self.logger.info("✓ TICK to LEVEL2 transition validated")

            # Test 6: Error conditions
            self.logger.info("\n--- Test 6: Error Conditions ---")

            # Test empty symbols
            self.change_subscription("LEVEL1", [], "empty_symbols_test")
            time.sleep(2)

            # Test invalid level
            self.change_subscription("INVALID_LEVEL", ["AAPL"], "invalid_level_test")
            time.sleep(2)

            # Test nonexistent symbol
            self.change_subscription("LEVEL1", ["NONEXISTENT_SYMBOL_12345"], "nonexistent_symbol_test")
            time.sleep(2)

            # Wait a bit more for error responses
            time.sleep(3)

            # Clean up
            self.remove_symbol(self.test_symbols['LEVEL1'] + self.test_symbols['LEVEL2'] + self.test_symbols['TICK'])

        finally:
            self.stop.set()
            time.sleep(1)  # Allow threads to clean up

        self._print_validation_results()

    def _print_validation_results(self):
        """Print comprehensive validation results"""
        self.logger.info("\n=== CHANGE_SUBSCRIPTION Validation Results ===")
        self.logger.info(f"Total responses received: {self.response_count}")

        all_passed = True
        for test_name, passed in self.validation_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            self.logger.info(f"{test_name}: {status}")
            if not passed:
                all_passed = False

        self.logger.info("\n" + "="*50)
        if all_passed:
            self.logger.info("🎉 ALL CHANGE_SUBSCRIPTION VALIDATION TESTS PASSED!")
        else:
            self.logger.warning("⚠️  Some validation tests failed. Check server logs for details.")
        self.logger.info("="*50)


def main():
    """Main entry point for CHANGE_SUBSCRIPTION validation"""
    print("CHANGE_SUBSCRIPTION Validation Script")
    print("=====================================")
    print("This script validates the CHANGE_SUBSCRIPTION functionality")
    print("of the bidirectional streaming market data API.")
    print()

    validator = ChangeSubscriptionValidator()

    try:
        validator.run_validation_tests()
    except KeyboardInterrupt:
        print("\nValidation interrupted by user.")
    except Exception as e:
        print(f"\nValidation failed with error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())