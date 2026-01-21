#!/usr/bin/env python3
"""
Streaming API Client - Python Implementation
==========================================

Command-line application for bidirectional streaming market data operations.
Supports adding/removing symbols, checking status, and changing subscriptions.

This script mirrors the functionality of the C# StreamingClientApp with:
- Modular architecture (RequestHandler, StatusManager, SymbolManager)
- Comprehensive logging for all subscription operations
- Bidirectional streaming with proper error handling
- Interactive command-line interface

Author: SS&C Eze Software
Date: December 1, 2025
"""

import asyncio
import concurrent.futures
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple

# EMSX API imports
from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
import market_data_pb2_grpc


class StreamingLogger:
    """Enhanced file logger for streaming market data operations."""

    def __init__(self, log_directory: str = "logs"):
        """Initialize the streaming logger with timestamped log file."""
        self.log_directory = log_directory
        self._setup_logging()

    def _setup_logging(self):
        """Configure comprehensive logging for the streaming client."""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_directory, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"streaming_client_{timestamp}.log"
        self.log_file_path = os.path.join(self.log_directory, log_filename)

        # Configure logger
        self.logger = logging.getLogger("StreamingClient")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # File handler for detailed logging
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info("=== Streaming API Client Log Started ===")
        self.logger.info(f"Log file: {self.log_file_path}")
        self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def log_subscription(self, operation: str, symbols: List[str], market_data_level: str = ""):
        """Log subscription operations (add, remove, change)."""
        symbol_list = ", ".join(symbols) if symbols else "NONE"
        level_info = f" | Level: {market_data_level}" if market_data_level else ""
        self.logger.info(f"SUBSCRIPTION | {operation} | Symbols: [{symbol_list}]{level_info}")

    def log_subscription_request(self, request_type: str, symbols: List[str],
                               market_data_level: str, user_token: str):
        """Log detailed subscription request information."""
        symbol_list = ", ".join(symbols) if symbols else "NONE"
        level_info = f" | Level: {market_data_level}" if market_data_level else ""
        token_info = f" | Token: {user_token[:8]}..." if user_token else " | Token: None"
        self.logger.info(f"REQUEST | {request_type} | Symbols: [{symbol_list}]{level_info}{token_info}")

    def log_streaming_response(self, response):
        """Log complete streaming response for debugging and action tracking."""
        try:
            response_str = str(response)
            # Truncate very long responses for readability
            if len(response_str) > 500:
                response_str = response_str[:500] + "..."
            self.logger.info(f"STREAMING_RESPONSE | {response_str}")
        except Exception as e:
            self.logger.error(f"Error logging streaming response: {e}")

    def log_market_data(self, symbol: str, data_type: str, data: str):
        """Log market data in structured format."""
        self.logger.info(f"MARKET_DATA | {symbol} | {data_type} | {data}")

    def log_status(self, status: str):
        """Log status updates."""
        self.logger.info(f"STATUS | {status}")

    def log_error(self, error: str):
        """Log errors."""
        self.logger.error(f"ERROR | {error}")

    def log_success(self, message: str):
        """Log success messages."""
        self.logger.info(f"SUCCESS | {message}")

    def log_message(self, message: str):
        """Log a general message."""
        self.logger.info(f"MESSAGE | {message}")

    @property
    def log_path(self) -> str:
        """Get the current log file path."""
        return self.log_file_path


class StreamingClient:
    """Core streaming client handling bidirectional communication."""

    def __init__(self, xapi_lib):
        self.xapi_lib = xapi_lib
        self.logger = StreamingLogger()
        self.active_subscriptions = {
            'LEVEL1': set(),
            'LEVEL2': set(),
            'TICK': set()
        }
        self.is_streaming = False
        self.streaming_call = None
        self.response_thread = None
        self.request_queue = queue.Queue()
        self.ready_event = threading.Event()
        self.stop_event = threading.Event()
        self.console_lock = threading.Lock()

    def add_subscriptions(self, symbols: List[str], market_data_level: str):
        """Add symbols to active subscriptions tracking."""
        if market_data_level in self.active_subscriptions:
            self.active_subscriptions[market_data_level].update(symbols)

    def remove_subscriptions(self, symbols: List[str]):
        """Remove symbols from active subscriptions tracking."""
        for level_symbols in self.active_subscriptions.values():
            level_symbols.difference_update(symbols)

    def update_subscriptions(self, symbols: List[str], market_data_level: str):
        """Update subscription level for symbols."""
        # Remove from all levels first
        for level_symbols in self.active_subscriptions.values():
            level_symbols.difference_update(symbols)
        # Add to new level
        if market_data_level in self.active_subscriptions:
            self.active_subscriptions[market_data_level].update(symbols)

    async def send_request_async(self, request):
        """Send a request through the streaming call."""
        if self.is_streaming:
            self.request_queue.put(request)

    async def start_streaming_async(self):
        """Start the bidirectional streaming connection."""
        try:
            self.logger.log_status("Starting bidirectional streaming connection...")

            # Set streaming flag
            self.is_streaming = True

            # Get the market data service stub
            stub = self.xapi_lib._mkt_data_svc_stub

            # Create synchronous request generator
            def request_generator():
                # Send initial request
                yield market_data_pb2.MarketDataStreamRequest(
                    UserToken=self.xapi_lib.userToken,
                    RequestType="INIT",
                    Request=True
                )
                # Process additional requests from queue
                while self.is_streaming:
                    try:
                        request = self.request_queue.get(timeout=0.1)
                        yield request
                    except queue.Empty:
                        continue

            # Start bidirectional streaming
            self.streaming_call = stub.StreamMarketData(request_generator())

            # Start response processing thread
            self.response_thread = threading.Thread(target=self._process_responses_sync)
            self.response_thread.daemon = True
            self.response_thread.start()

            # Wait for ready signal
            if self.ready_event.wait(timeout=10.0):
                self.logger.log_success("Bidirectional streaming connection established")
            else:
                raise TimeoutError("Timeout waiting for streaming connection to be ready")

        except Exception as e:
            self.logger.log_error(f"Failed to start streaming: {e}")
            raise

    async def stop_streaming_async(self):
        """Stop the streaming connection."""
        try:
            self.logger.log_status("Stopping streaming connection...")

            self.is_streaming = False

            # Wait for response thread to finish
            if self.response_thread and self.response_thread.is_alive():
                self.response_thread.join(timeout=5.0)

            self.logger.log_success("Streaming connection stopped")

        except Exception as e:
            self.logger.log_error(f"Error stopping streaming: {e}")

    def _process_responses_sync(self):
        """Process streaming responses synchronously."""
        try:
            for response in self.streaming_call:
                self._handle_response_sync(response)
        except Exception as e:
            self.logger.log_error(f"Error in synchronous response processing: {e}")

    def _handle_response_sync(self, response):
        """Handle individual streaming responses synchronously."""
        try:
            # Log the complete streaming response for debugging and action tracking
            self.logger.log_streaming_response(response)

            # Check for acknowledgments
            if hasattr(response, 'Acknowledgement') and response.Acknowledgement:
                ack = response.Acknowledgement
                if ack.ServerResponse == "success":
                    self.logger.log_success(f"Server acknowledgment: {ack.Message}")
                    if not self.ready_event.is_set():
                        self.ready_event.set()
                else:
                    self.logger.log_error(f"Server error: {ack.Message}")

            # Process different response types
            response_type = getattr(response, 'ResponseType', '')

            if response_type == "LEVEL1_DATA":
                self._process_level1_data_sync(response)
            elif response_type == "LEVEL2_DATA":
                self._process_level2_data_sync(response)
            elif response_type == "TICK_DATA":
                self._process_tick_data_sync(response)
            elif response_type == "STATUS_UPDATE":
                self.logger.log_status(f"Status update: {getattr(response, 'StatusMessage', 'Unknown')}")
            else:
                self.logger.log_message(f"Unknown response type: {response_type}")

        except Exception as e:
            self.logger.log_error(f"Error handling response: {e}")

    def _process_level1_data_sync(self, response):
        """Process Level1 market data synchronously."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')

            # Extract price data
            bid = getattr(response, 'Bid', None)
            ask = getattr(response, 'Ask', None)
            last = getattr(response, 'Trdprc1', None)

            bid_val = bid.DecimalValue if bid and hasattr(bid, 'DecimalValue') and not getattr(bid, 'Isnull', True) else 0.0
            ask_val = ask.DecimalValue if ask and hasattr(ask, 'DecimalValue') and not getattr(ask, 'Isnull', True) else 0.0
            last_val = last.DecimalValue if last and hasattr(last, 'DecimalValue') and not getattr(last, 'Isnull', True) else 0.0

            data = f"Bid: {bid_val:.2f} | Ask: {ask_val:.2f} | Last: {last_val:.2f}"
            self.logger.log_market_data(symbol, "LEVEL1", data)

        except Exception as e:
            self.logger.log_error(f"Error processing Level1 data: {e}")

    def _process_level2_data_sync(self, response):
        """Process Level2 market data synchronously."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')
            data = f"Level2 data for {symbol}"
            self.logger.log_market_data(symbol, "LEVEL2", data)
        except Exception as e:
            self.logger.log_error(f"Error processing Level2 data: {e}")

    def _process_tick_data_sync(self, response):
        """Process tick data synchronously."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')
            data = f"Tick data for {symbol}"
            self.logger.log_market_data(symbol, "TICK", data)
        except Exception as e:
            self.logger.log_error(f"Error processing tick data: {e}")

    async def _process_level1_data(self, response):
        """Process Level1 market data."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')

            # Extract price data
            bid = getattr(response, 'Bid', None)
            ask = getattr(response, 'Ask', None)
            last = getattr(response, 'Trdprc1', None)

            bid_val = bid.DecimalValue if bid and hasattr(bid, 'DecimalValue') and not getattr(bid, 'Isnull', True) else 0.0
            ask_val = ask.DecimalValue if ask and hasattr(ask, 'DecimalValue') and not getattr(ask, 'Isnull', True) else 0.0
            last_val = last.DecimalValue if last and hasattr(last, 'DecimalValue') and not getattr(last, 'Isnull', True) else 0.0

            data = f"Bid: {bid_val:.2f} | Ask: {ask_val:.2f} | Last: {last_val:.2f}"
            self.logger.log_market_data(symbol, "LEVEL1", data)

        except Exception as e:
            self.logger.log_error(f"Error processing Level1 data: {e}")

    async def _process_level2_data(self, response):
        """Process Level2 market data."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')
            data = f"Level2 data for {symbol}"
            self.logger.log_market_data(symbol, "LEVEL2", data)
        except Exception as e:
            self.logger.log_error(f"Error processing Level2 data: {e}")

    async def _process_tick_data(self, response):
        """Process tick data."""
        try:
            symbol = getattr(response, 'DispName', '') or getattr(response, 'SymbolDesc', '')
            data = f"Tick data for {symbol}"
            self.logger.log_market_data(symbol, "TICK", data)
        except Exception as e:
            self.logger.log_error(f"Error processing tick data: {e}")

    def log_message(self, message: str):
        """Log a general message."""
        self.logger.logger.info(message)


class RequestHandler:
    """Handles sending subscription requests to the streaming service."""

    def __init__(self, streaming_client: StreamingClient):
        self.streaming_client = streaming_client
        self.xapi_lib = EMSXAPILibrary.get()

    async def add_symbols_async(self, symbols: List[str], market_data_level: str):
        """Send a subscription request for adding symbols."""
        self.streaming_client.logger.log_subscription("ADD_SYMBOL", symbols, market_data_level)
        await self._send_subscription_request("ADD_SYMBOL", symbols, market_data_level)
        self.streaming_client.add_subscriptions(symbols, market_data_level)

    async def remove_symbols_async(self, symbols: List[str]):
        """Send a subscription request for removing symbols."""
        self.streaming_client.logger.log_subscription("REMOVE_SYMBOL", symbols)
        await self._send_subscription_request("REMOVE_SYMBOL", symbols, "")
        self.streaming_client.remove_subscriptions(symbols)

    async def change_subscription_async(self, symbols: List[str], market_data_level: str):
        """Send a subscription request for changing subscription levels."""
        self.streaming_client.logger.log_subscription("CHANGE_SUBSCRIPTION", symbols, market_data_level)
        await self._send_subscription_request("CHANGE_SUBSCRIPTION", symbols, market_data_level)
        self.streaming_client.update_subscriptions(symbols, market_data_level)

    async def _send_subscription_request(self, request_type: str, symbols: List[str], market_data_level: str):
        """Send a subscription request to the server."""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapi_lib.userToken
        request.RequestType = request_type
        request.Request = True
        request.Advise = True

        if symbols:
            request.Symbols.extend(symbols)

        if market_data_level:
            request.MarketDataLevel = market_data_level

        # Log the detailed request
        self.streaming_client.logger.log_subscription_request(
            request_type, symbols, market_data_level, request.UserToken
        )

        await self.streaming_client.send_request_async(request)

        # Log the action performed
        symbol_list = ", ".join(symbols) if symbols else "NONE"
        self.streaming_client.logger.log_status(f"Action performed: {request_type} | Level: {market_data_level} | Symbols: [{symbol_list}]")


class SymbolManager:
    """Handles user input for symbol management operations."""

    def __init__(self, request_handler: RequestHandler):
        self.request_handler = request_handler

    async def handle_add_symbols_async(self):
        """Handle adding symbols to the stream."""
        symbols, level = self._get_symbol_input("add")
        if not symbols:
            return

        await self.request_handler.add_symbols_async(symbols, level)
        self.streaming_client.logger.log_success(f"Added symbols: {', '.join(symbols)} for {level} data")

    async def handle_remove_symbols_async(self):
        """Handle removing symbols from the stream."""
        symbols = self._get_symbols_input("remove")
        if not symbols:
            return

        await self.request_handler.remove_symbols_async(symbols)
        self.streaming_client.logger.log_success(f"Removed symbols: {', '.join(symbols)} from streaming")

    async def handle_change_subscription_async(self):
        """Handle changing subscription levels for symbols."""
        symbols = self._get_symbols_input("change")
        if not symbols:
            return

        level = self._get_level_input()
        if not level:
            return

        await self.request_handler.change_subscription_async(symbols, level)
        self.streaming_client.logger.log_success(f"Changed subscription for symbols: {', '.join(symbols)} to {level}")

    def _get_symbol_input(self, action: str) -> Tuple[List[str], str]:
        """Get symbol and level input from user."""
        symbols_input = input(f"Enter symbols to {action} (comma-separated): ").strip()
        if not symbols_input:
            self.streaming_client.logger.log_status("No symbols entered for operation")
            return [], ""

        symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

        level = self._get_level_input()
        if not level:
            return [], ""

        return symbols, level

    def _get_symbols_input(self, action: str) -> List[str]:
        """Get symbols input from user."""
        symbols_input = input(f"Enter symbols to {action} (comma-separated): ").strip()
        if not symbols_input:
            self.streaming_client.logger.log_status("No symbols entered for operation")
            return []

        return [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

    def _get_level_input(self) -> str:
        """Get market data level input from user."""
        print("\nAvailable market data levels:")
        print("1. LEVEL1 - Basic price data (bid, ask, last)")
        print("2. LEVEL2 - Market depth data")
        print("3. TICK - Individual trade ticks")

        while True:
            choice = input("Select level (1-3): ").strip()
            if choice == "1":
                return "LEVEL1"
            elif choice == "2":
                return "LEVEL2"
            elif choice == "3":
                return "TICK"
            else:
                self.streaming_client.logger.log_error("Invalid level choice selected")


class StatusManager:
    """Handles status display and monitoring operations."""

    def __init__(self, request_handler: RequestHandler, streaming_client: StreamingClient):
        self.request_handler = request_handler
        self.streaming_client = streaming_client

    async def handle_check_status_async(self):
        """Handle status check request."""
        # Display active subscriptions
        status_info = []
        for level, symbols in self.streaming_client.active_subscriptions.items():
            if symbols:
                status_info.append(f"{level}: {', '.join(sorted(symbols))}")
            else:
                status_info.append(f"{level}: None")

        # Display connection status
        connection_status = "Connected" if self.streaming_client.ready_event.is_set() else "Disconnected"
        status_info.append(f"Connection: {connection_status}")
        status_info.append(f"Log File: {self.streaming_client.logger.log_path}")

        # Log the complete status
        self.streaming_client.logger.log_status(f"Status check | {' | '.join(status_info)}")

        # Still display to user for interactive experience
        print("\n=== Current Streaming Status ===")
        print("Active Subscriptions:")
        for level, symbols in self.streaming_client.active_subscriptions.items():
            if symbols:
                print(f"  {level}: {', '.join(sorted(symbols))}")
            else:
                print(f"  {level}: None")
        print(f"Connection Status: {connection_status}")
        print(f"Log File: {self.streaming_client.logger.log_path}")
        print("================================")


async def show_command_menu_async(symbol_manager: SymbolManager, status_manager: StatusManager):
    """Display and handle the interactive command menu."""
    while True:
        print("\n=== Streaming Market Data Client ===")
        print("Available commands:")
        print("1. Add symbols to stream")
        print("2. Remove symbols from stream")
        print("3. Change subscription level")
        print("4. Check status")
        print("5. Exit")
        print("==================================")

        choice = input("Enter your choice (1-5): ").strip()

        try:
            if choice == "1":
                await symbol_manager.handle_add_symbols_async()
            elif choice == "2":
                await symbol_manager.handle_remove_symbols_async()
            elif choice == "3":
                await symbol_manager.handle_change_subscription_async()
            elif choice == "4":
                await status_manager.handle_check_status_async()
            elif choice == "5":
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please select 1-5.")
        except Exception as e:
            print(f"Error processing command: {e}")


async def main():
    """Main application entry point."""
    print("=== Bidirectional Streaming Market Data Client (Python) ===")
    print("Command-line interface for market data operations")
    print()

    streaming_client = None

    try:
        # Initialize EMSXAPILibrary
        EMSXAPILibrary.create("../config.cfg")
        xapi_lib = EMSXAPILibrary.get()

        # Perform login
        xapi_lib.login()
        if not xapi_lib.userToken:
            print("Login failed. Please check your configuration.")
            return

        print("Successfully logged in and connected to EMS XAPI server.")

        # Create components
        streaming_client = StreamingClient(xapi_lib)
        request_handler = RequestHandler(streaming_client)
        symbol_manager = SymbolManager(request_handler)
        status_manager = StatusManager(request_handler, streaming_client)

        print(f"Streaming data will be logged to: {streaming_client.logger.log_path}")
        print()

        # Start the streaming connection
        await streaming_client.start_streaming_async()

        # Show the command menu
        await show_command_menu_async(symbol_manager, status_manager)

        # Stop streaming and cleanup
        await streaming_client.stop_streaming_async()

        print("\n=== Streaming client completed successfully ===")

    except Exception as e:
        print(f"Error in streaming client: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure proper cleanup
        if streaming_client:
            await streaming_client.stop_streaming_async()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())