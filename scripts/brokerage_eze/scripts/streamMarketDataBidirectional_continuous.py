"""
Continuous/Long-Running Support Script for StreamMarketData Bidirectional API

This script extends the basic streamMarketDataBidirectional.py example with:
- Infinite loop support (runs until manually interrupted)
- Configurable runtime (hours-based execution like SSNC client)
- Automatic reconnection on failures
- Symbol rotation and cycling
- Health monitoring and statistics
- Graceful shutdown handling

Usage Examples:
    # Run infinitely until Ctrl+C
    python streamMarketDataBidirectional_continuous.py --mode infinite

    # Run for 8 hours with cycles
    python streamMarketDataBidirectional_continuous.py --mode timed --hours 8

    # Run with custom configuration
    python streamMarketDataBidirectional_continuous.py --mode timed --hours 12 --cycle-delay 300
"""

from datetime import datetime, timedelta
from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time
import logging
from logging.handlers import RotatingFileHandler
import queue
import argparse
import signal
import sys
import os


class ContinuousStreamMarketData:
    """
    Extended StreamMarketData client with continuous/infinite running capabilities.
    Supports long-running operations with automatic recovery and health monitoring.
    """

    # Constants for commonly used symbols
    VOD_LSE = "VOD.LSE"

    def __init__(self, enable_reconnection=True):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()
        self.request_queue = queue.Queue()
        self.active_subscriptions = {
            'LEVEL1': set(),
            'LEVEL2': set(),
            'TICK': set()
        }

        # Configuration
        self.enable_reconnection = enable_reconnection

        # Runtime tracking
        self.total_cycles = 0
        self.start_time = None
        self.last_successful_cycle = None
        self.total_messages_received = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

        # Message sampling for log reduction (log every Nth message)
        self.level1_counter = 0
        self.level2_counter = 0
        self.tick_counter = 0
        self.level1_log_every = 50  # Log every 50th Level1 update
        self.level2_log_every = 20  # Log every 20th Level2 update
        self.tick_log_every = 100   # Log every 100th Tick update

        # Symbol pools for rotation
        self.symbol_pools = {
            'LEVEL1': [
                ["AAPL", "MSFT", "GOOGL"],
                ["NVDA", "AMD", self.VOD_LSE],
                ["TSLA", "F", "GM"],
                ["JPM", "BAC", "WFC"],
                ["XOM", "CVX", "COP"]
            ],
            'LEVEL2': [
                ["AAPL", "MSFT"],
                ["NVDA", self.VOD_LSE],
                ["TSLA", "F"]
            ],
            'TICK': [
                [self.VOD_LSE],
                ["BP.LSE"],
                ["HSBC.LSE"]
            ]
        }
        self.current_pool_index = 0

        # Setup structured logging with rotation to prevent large files
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Rotating file handler: max 10MB per file, keep 5 backup files
        log_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Main log with rotation
        file_handler = RotatingFileHandler(
            'StreamMarketData_Continuous.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)

        # Separate summary log for statistics only (smaller, no rotation needed)
        summary_handler = logging.FileHandler('StreamMarketData_Summary.log')
        summary_handler.setLevel(logging.WARNING)  # Only warnings and errors for summary
        summary_handler.setFormatter(log_formatter)
        self.logger.addHandler(summary_handler)

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
        print(f"\n[STOP] Received {signal_name}, initiating graceful shutdown...")
        self.logger.info(f"Received {signal_name}, shutting down gracefully")
        self.stop.set()

    def start_bidirectional_stream(self):
        """Start the bidirectional streaming connection"""
        print("[START] Starting bidirectional StreamMarketData connection...")

        # Validate userToken before starting stream
        if self.xapiLib.userToken is None:
            raise ValueError("UserToken is None - authentication required before starting bidirectional stream")
        if not isinstance(self.xapiLib.userToken, str) or self.xapiLib.userToken.strip() == "":
            raise ValueError("UserToken is empty or invalid - authentication required before starting bidirectional stream")

        # Start the bidirectional stream thread
        self.stream_thread = Thread(target=self._handle_bidirectional_stream, daemon=True)
        self.stream_thread.start()

        # Wait for stream to be ready
        if not self.ready.wait(timeout=10.0):
            raise TimeoutError("Timeout waiting for bidirectional stream to initialize")
        print("[OK] Bidirectional stream is ready!")

    def add_level1_symbols(self, symbols):
        """Add symbols for Level1 market data"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = "LEVEL1"
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)
        self.active_subscriptions['LEVEL1'].update(symbols)

        print(f"[LEVEL1] Adding Level1 symbols: {', '.join(symbols)}")
        self.logger.info(f"Level1 ADD_SYMBOL request: {symbols}")

    def add_level2_symbols(self, symbols):
        """Add symbols for Level2 market data"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = "LEVEL2"
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)
        self.active_subscriptions['LEVEL2'].update(symbols)

        print(f"[LEVEL2] Adding Level2 symbols: {', '.join(symbols)}")
        self.logger.info(f"Level2 ADD_SYMBOL request: {symbols}")

    def add_tick_symbols(self, symbols):
        """Add symbols for Tick data"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = "TICK"
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)
        self.active_subscriptions['TICK'].update(symbols)

        print(f"[TICK] Adding Tick symbols: {', '.join(symbols)}")
        self.logger.info(f"Tick ADD_SYMBOL request: {symbols}")

    def change_subscription(self, market_data_level, new_symbols):
        """Change subscription to new set of symbols"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "CHANGE_SUBSCRIPTION"
        request.Symbols.extend(new_symbols)
        request.MarketDataLevel = market_data_level
        request.Request = True
        request.Advise = True

        self.request_queue.put(request)

        if market_data_level in self.active_subscriptions:
            self.active_subscriptions[market_data_level] = set(new_symbols)

        print(f"[CHANGE] Changing {market_data_level} subscription to: {', '.join(new_symbols)}")
        self.logger.info(f"{market_data_level} CHANGE_SUBSCRIPTION request: {new_symbols}")

    def _handle_bidirectional_stream(self):
        """Handle the bidirectional streaming connection"""
        try:
            # Create the bidirectional stream
            def request_generator():
                # Send initial authentication request
                initial_request = market_data_pb2.MarketDataStreamRequest()
                initial_request.UserToken = self.xapiLib.userToken
                initial_request.RequestType = "INIT"
                self.logger.info(f"Sending initial authentication request")
                yield initial_request

                # Mark stream as ready
                self.ready.set()

                # Process subsequent requests
                while not self.stop.is_set():
                    try:
                        request = self.request_queue.get(timeout=1.0)
                        self.logger.info(f"Sending request: {request.RequestType} - {request.MarketDataLevel}")
                        yield request
                        self.request_queue.task_done()
                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.logger.error(f"Error in request generator: {e}")
                        break

            # Start the bidirectional stream
            response_stream = self.xapiLib.get_market_data_service_stub().StreamMarketData(request_generator())

            print("[OK] Bidirectional stream connection established")
            self.logger.info("Bidirectional stream connection established")

            # Process responses
            for response in response_stream:
                if self.stop.is_set():
                    print('[STOP] Stopping bidirectional stream...')
                    break

                try:
                    self._process_stream_response(response)
                    self.total_messages_received += 1
                    self.consecutive_failures = 0  # Reset on successful processing
                except Exception as e:
                    error_msg = f"Error processing stream response: {e}"
                    print(error_msg)
                    self.logger.error(error_msg)
                    self.consecutive_failures += 1

        except Exception as e:
            error_msg = f"Bidirectional stream error: {e}"
            print(error_msg)
            self.logger.error(error_msg)
            self.consecutive_failures += 1

    def _process_stream_response(self, response):
        """Process different types of stream responses"""
        if response.Acknowledgement.ServerResponse != "success":
            error_msg = f"Server error: {response.Acknowledgement.ServerResponse} - {response.Acknowledgement.Message}"
            print(error_msg)
            self.logger.error(error_msg)
            return

        response_type = response.ResponseType

        if response_type == "LEVEL1_DATA":
            self._process_level1_data(response)
        elif response_type == "LEVEL2_DATA":
            self._process_level2_data(response)
        elif response_type == "TICK_DATA":
            self._process_tick_data(response)
        elif response_type == "STATUS_UPDATE":
            self._process_status_update(response)

    def _is_meaningful_level1_update(self, response):
        """Check if Level1 update contains meaningful data"""
        ask_val = response.Ask.DecimalValue if response.Ask and not response.Ask.Isnull else 0
        bid_val = response.Bid.DecimalValue if response.Bid and not response.Bid.Isnull else 0
        last_val = response.Trdprc1.DecimalValue if response.Trdprc1 and not response.Trdprc1.Isnull else 0
        return not (ask_val == 0 and bid_val == 0 and last_val == 0 and not response.SymbolDesc)

    def _process_level1_data(self, response):
        """Process Level1 market data with sampling to reduce log volume"""
        if not self._is_meaningful_level1_update(response):
            return

        self.level1_counter += 1

        # Only log every Nth message to prevent log spam
        if self.level1_counter % self.level1_log_every == 0:
            message = "LEVEL1 [DATA] Symbol: {}, Ask: {}, Bid: {}, Last: {} [Sample {}/{}]".format(
                response.SymbolDesc if response.SymbolDesc else response.DispName,
                response.Ask.DecimalValue if response.Ask and not response.Ask.Isnull else "N/A",
                response.Bid.DecimalValue if response.Bid and not response.Bid.Isnull else "N/A",
                response.Trdprc1.DecimalValue if response.Trdprc1 and not response.Trdprc1.Isnull else "N/A",
                self.level1_counter,
                self.level1_log_every
            )
            self.logger.info(message)
            # Only print to console occasionally (every 100th)
            if self.level1_counter % (self.level1_log_every * 2) == 0:
                print(message)

    def _is_meaningful_level2_update(self, response):
        """Check if Level2 update contains meaningful data"""
        bid_val = response.MktMkrBid.DecimalValue if response.MktMkrBid and not response.MktMkrBid.Isnull else 0
        ask_val = response.MktMkrAsk.DecimalValue if response.MktMkrAsk and not response.MktMkrAsk.Isnull else 0
        bid_size = response.MktMkrBidsize.value if response.MktMkrBidsize else 0
        ask_size = response.MktMkrAsksize.value if response.MktMkrAsksize else 0
        return not (bid_val == 0 and ask_val == 0 and bid_size == 0 and ask_size == 0)

    def _process_level2_data(self, response):
        """Process Level2 market data with sampling to reduce log volume"""
        if not self._is_meaningful_level2_update(response):
            return

        self.level2_counter += 1

        # Only log every Nth message to prevent log spam
        if self.level2_counter % self.level2_log_every == 0:
            message = "LEVEL2 [DATA] Symbol: {}, Market Maker: {}, Bid: {}, Ask: {}, Sizes: {}/{} [Sample {}/{}]".format(
                response.DispName,
                response.MktMkrId,
                response.MktMkrBid.DecimalValue if response.MktMkrBid and not response.MktMkrBid.Isnull else "N/A",
                response.MktMkrAsk.DecimalValue if response.MktMkrAsk and not response.MktMkrAsk.Isnull else "N/A",
                response.MktMkrBidsize.value if response.MktMkrBidsize else "N/A",
                response.MktMkrAsksize.value if response.MktMkrAsksize else "N/A",
                self.level2_counter,
                self.level2_log_every
            )
            self.logger.info(message)
            # Only print to console occasionally (every 40th)
            if self.level2_counter % (self.level2_log_every * 2) == 0:
                print(message)

    def _process_tick_data(self, response):
        """Process Tick data with aggressive sampling to reduce log volume"""
        if response.Count > 0:
            self.tick_counter += response.Count

            # Only log every Nth batch of ticks
            if self.tick_counter % self.tick_log_every < response.Count:
                tick_types = {0: "TRADE", 1: "BID", 2: "ASK", 3: "REGIONAL_BID", 4: "REGIONAL_ASK"}
                # Only log first 3 ticks from sampled batch
                max_ticks_to_log = 3

                summary_msg = f"TICK [BATCH] Batch for {response.DispName}: {response.Count} ticks [Total processed: {self.tick_counter}]"
                self.logger.info(summary_msg)

                # Log sample ticks
                for i in range(min(max_ticks_to_log, len(response.TrdPrc1List), response.Count)):
                    tick_type = tick_types.get(response.TickTypeList[i], f"UNKNOWN({response.TickTypeList[i]})")
                    price = response.TrdPrc1List[i].DecimalValue if not response.TrdPrc1List[i].Isnull else "N/A"
                    volume = response.TrdVol1List[i] if i < len(response.TrdVol1List) else "N/A"

                    message = "TICK [SAMPLE]   Sample {}: Type: {}, Price: {}, Volume: {}".format(
                        i+1, tick_type, price, volume
                    )
                    self.logger.info(message)

                # Only print to console very rarely (every 500th tick)
                if self.tick_counter % 500 < response.Count:
                    print(summary_msg)

    def _process_status_update(self, response):
        """Process status updates"""
        message = f"STATUS [INFO] {response.StatusMessage}"
        print(message)
        self.logger.info(message)

    def rotate_symbols(self):
        """Rotate to next symbol pool"""
        self.current_pool_index = (self.current_pool_index + 1) % len(self.symbol_pools['LEVEL1'])

        print(f"\n[CHANGE] Rotating to symbol pool #{self.current_pool_index + 1}")
        self.logger.info(f"Rotating to symbol pool #{self.current_pool_index + 1}")

        # Change subscriptions to new symbol pools
        self.change_subscription("LEVEL1", self.symbol_pools['LEVEL1'][self.current_pool_index % len(self.symbol_pools['LEVEL1'])])
        self.change_subscription("LEVEL2", self.symbol_pools['LEVEL2'][self.current_pool_index % len(self.symbol_pools['LEVEL2'])])
        self.change_subscription("TICK", self.symbol_pools['TICK'][self.current_pool_index % len(self.symbol_pools['TICK'])])

    def _check_connection_health(self):
        """Check if connection is healthy"""
        return (hasattr(self.xapiLib, 'userToken') and
                self.xapiLib.userToken is not None and
                not self.stop.is_set())

    def _attempt_reconnection(self):
        """Attempt to reconnect"""
        try:
            print("[CHANGE] Attempting reconnection...")
            self.logger.info("Attempting reconnection")

            # Stop current stream
            self.stop.set()
            if hasattr(self, 'stream_thread'):
                self.stream_thread.join(timeout=5.0)

            # Reset events
            self.ready.clear()
            self.stop.clear()

            # Logout and close channel
            try:
                self.xapiLib.logout()
                self.xapiLib.close_channel()
            except Exception as e:
                self.logger.warning(f"Error during logout/close in reconnection: {e}")
                pass

            time.sleep(5)

            # Reconnect
            self.xapiLib.login()
            self.start_bidirectional_stream()

            print("[OK] Reconnection successful")
            self.logger.info("Reconnection successful")
            return True

        except Exception as e:
            print(f"[ERROR] Reconnection failed: {e}")
            self.logger.error(f"Reconnection failed: {e}")
            return False

    def _log_statistics(self):
        """Log runtime statistics"""
        if self.start_time:
            runtime_hours = (time.time() - self.start_time) / 3600
            avg_messages_per_cycle = self.total_messages_received / self.total_cycles if self.total_cycles > 0 else 0

            print(f"\n[LEVEL2] === Runtime Statistics ===")
            print(f"   Total cycles: {self.total_cycles}")
            print(f"   Runtime: {runtime_hours:.2f} hours")
            print(f"   Total messages: {self.total_messages_received}")
            print(f"   Level1: {self.level1_counter} (log every {self.level1_log_every})")
            print(f"   Level2: {self.level2_counter} (log every {self.level2_log_every})")
            print(f"   Ticks: {self.tick_counter} (log every {self.tick_log_every})")
            print(f"   Avg messages/cycle: {avg_messages_per_cycle:.1f}")
            print(f"   Consecutive failures: {self.consecutive_failures}")
            print(f"   Active subscriptions: {sum(len(v) for v in self.active_subscriptions.values())}")
            print(f"================================\n")

            self.logger.info(f"Statistics - Cycles: {self.total_cycles}, Runtime: {runtime_hours:.2f}h, "
                           f"Messages: {self.total_messages_received}, Failures: {self.consecutive_failures}")

    def _setup_initial_stream(self):
        """Setup initial login and stream for continuous operation"""
        print("\n[LOGIN] Logging in...")
        self.xapiLib.login()
        print("[OK] Successfully logged in")

        print("\n[START] Starting bidirectional stream...")
        self.start_bidirectional_stream()

        print("\n[LEVEL2] Setting up initial subscriptions...")
        self.add_level1_symbols(self.symbol_pools['LEVEL1'][0])
        self.add_level2_symbols(self.symbol_pools['LEVEL2'][0])
        self.add_tick_symbols(self.symbol_pools['TICK'][0])

    def _should_attempt_recovery(self):
        """Check if recovery should be attempted based on failure count"""
        return self.consecutive_failures >= self.max_consecutive_failures

    def _perform_recovery_attempt(self):
        """Attempt to recover from failures"""
        if self.enable_reconnection and self._attempt_reconnection():
            self.consecutive_failures = 0
            return True
        return False

    def _handle_connection_failure(self):
        """Handle connection health failure"""
        if self.enable_reconnection and not self._attempt_reconnection():
            print("[ERROR] Unable to maintain connection. Exiting.")
            return False
        return True

    def _handle_cycle_failure_recovery(self):
        """Handle recovery from consecutive failures"""
        print(f"[ERROR] Too many consecutive failures ({self.consecutive_failures}). Attempting recovery...")
        if not self._perform_recovery_attempt():
            print("[ERROR] Recovery failed. Exiting.")
            return False
        return True

    def _perform_cycle_operations(self, cycle_delay, rotate_symbols):
        """Perform main cycle operations"""
        # Validate cycle_delay to prevent negative sleep times
        if cycle_delay < 0:
            raise ValueError(f"cycle_delay cannot be negative, got {cycle_delay}")
            
        self.total_cycles += 1
        cycle_start = time.time()

        # Check connection health
        if not self._check_connection_health():
            if not self._handle_connection_failure():
                return False

        # Check consecutive failures
        if self._should_attempt_recovery():
            if not self._handle_cycle_failure_recovery():
                return False

        # Rotate symbols periodically (every 10 cycles)
        if rotate_symbols and self.total_cycles % 10 == 0:
            self.rotate_symbols()

        # Log statistics
        self._log_statistics()

        # Wait for next cycle
        elapsed = time.time() - cycle_start
        sleep_time = max(0, cycle_delay - elapsed)

        if sleep_time > 0:
            self._interruptible_sleep(sleep_time)

        self.last_successful_cycle = time.time()
        return True

    def _validate_run_parameters(self, cycle_delay, rotate_symbols, total_hours=None):
        """Validate parameters for run methods"""
        if cycle_delay is not None and (not isinstance(cycle_delay, (int, float)) or cycle_delay <= 0):
            raise ValueError(f"cycle_delay must be a positive number, got {cycle_delay}")
        
        if total_hours is not None and (not isinstance(total_hours, (int, float)) or total_hours <= 0):
            raise ValueError(f"total_hours must be a positive number, got {total_hours}")
        
        if not isinstance(rotate_symbols, bool):
            raise ValueError(f"rotate_symbols must be a boolean, got {rotate_symbols}")

    def run_infinite(self, cycle_delay=60, rotate_symbols=True):
        """
        Run continuously until manually interrupted (Ctrl+C)

        Args:
            cycle_delay: Seconds to wait between statistics logging
            rotate_symbols: Whether to rotate symbol pools periodically
        """
        # Validate input parameters
        self._validate_run_parameters(cycle_delay, rotate_symbols)
        
        print("=" * 70)
        print("INFINITE MODE - StreamMarketData Continuous")
        print("Press Ctrl+C to stop")
        print("=" * 70)

        self.start_time = time.time()

        try:
            # Initial login and stream setup
            self._setup_initial_stream()

            print(f"\n[OK] Infinite streaming started. Statistics logged every {cycle_delay}s (sampled data)")

            # Infinite loop
            while not self.stop.is_set():
                if not self._perform_cycle_operations(cycle_delay, rotate_symbols):
                    break

        except KeyboardInterrupt:
            print("\n[STOP] Infinite mode interrupted by user")
            self.logger.info("Infinite mode interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Error in infinite mode: {e}")
            self.logger.error(f"Error in infinite mode: {e}")
        finally:
            self._cleanup()

    def _calculate_remaining_time(self, end_time):
        """Calculate remaining time in hours"""
        return (end_time - time.time()) / 3600

    def _should_continue_timed_run(self, end_time):
        """Check if timed run should continue"""
        return time.time() < end_time and not self.stop.is_set()

    def _log_cycle_start(self, cycle_num, remaining_hours):
        """Log the start of a cycle"""
        print(f"\n[CHANGE] === Cycle {cycle_num} (Remaining: {remaining_hours:.2f}h) ===")
        self.logger.info(f"Cycle {cycle_num} started, remaining: {remaining_hours:.2f}h")

    def _handle_timed_recovery_resubscription(self):
        """Handle resubscription after recovery in timed mode"""
        if self._perform_recovery_attempt():
            # Resubscribe after reconnection (no pause for continuous flow)
            self.add_level1_symbols(self.symbol_pools['LEVEL1'][self.current_pool_index % len(self.symbol_pools['LEVEL1'])])
            self.add_level2_symbols(self.symbol_pools['LEVEL2'][self.current_pool_index % len(self.symbol_pools['LEVEL2'])])
            self.add_tick_symbols(self.symbol_pools['TICK'][self.current_pool_index % len(self.symbol_pools['TICK'])])
            return True
        return False

    def _perform_timed_cycle_operations(self, cycle_delay, rotate_symbols, end_time):
        """Perform main cycle operations for timed mode"""
        # Validate cycle_delay to prevent negative sleep times
        if cycle_delay < 0:
            raise ValueError(f"cycle_delay cannot be negative, got {cycle_delay}")
            
        self.total_cycles += 1
        cycle_start = time.time()

        remaining_hours = self._calculate_remaining_time(end_time)
        self._log_cycle_start(self.total_cycles, remaining_hours)

        # Check connection health
        if not self._check_connection_health():
            if not self._handle_connection_failure():
                return False

        # Check consecutive failures
        if self._should_attempt_recovery():
            if not self._handle_timed_recovery_resubscription():
                    print("[ERROR] Recovery failed. Exiting.")
                    return False        # Rotate symbols periodically (every 5 cycles)
        if rotate_symbols and self.total_cycles % 5 == 0:
            self.rotate_symbols()
            time.sleep(2)

        # Log statistics
        self._log_statistics()

        # Wait for next cycle
        remaining_time = end_time - time.time()
        if remaining_time <= 0:
            return False

        sleep_time = min(cycle_delay, remaining_time)
        print(f"[SLEEP] Waiting {sleep_time:.0f}s before next cycle...")
        self._interruptible_sleep(sleep_time)

        self.last_successful_cycle = time.time()
        return True

    def run_timed(self, total_hours=8.0, cycle_delay=300, rotate_symbols=True):
        """
        Run for a specified number of hours with periodic cycles

        Args:
            total_hours: Total runtime in hours
            cycle_delay: Seconds between cycles
            rotate_symbols: Whether to rotate symbol pools
        """
        # Validate input parameters
        self._validate_run_parameters(cycle_delay, rotate_symbols, total_hours)
        
        print("=" * 70)
        print(f"TIMED MODE - StreamMarketData Continuous ({total_hours} hours)")
        print("=" * 70)

        self.start_time = time.time()
        end_time = self.start_time + (total_hours * 3600)

        try:
            # Initial login and stream setup
            self._setup_initial_stream()

            print(f"\n[OK] Timed streaming started. Running for {total_hours} hours (sampled logging)")

            # Timed loop
            while self._should_continue_timed_run(end_time):
                if not self._perform_timed_cycle_operations(cycle_delay, rotate_symbols, end_time):
                    break

        except KeyboardInterrupt:
            print("\n[STOP] Timed mode interrupted by user")
            self.logger.info("Timed mode interrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Error in timed mode: {e}")
            self.logger.error(f"Error in timed mode: {e}")
        finally:
            total_runtime = (time.time() - self.start_time) / 3600
            print(f"\n[FINISH] Timed mode completed after {total_runtime:.2f} hours, {self.total_cycles} cycles")
            self.logger.info(f"Timed mode completed: {total_runtime:.2f}h, {self.total_cycles} cycles")
            self._cleanup()

    def _interruptible_sleep(self, duration):
        """Sleep that can be interrupted"""
        end_time = time.time() + duration
        while time.time() < end_time and not self.stop.is_set():
            sleep_chunk = min(10, end_time - time.time())
            if sleep_chunk > 0:
                time.sleep(sleep_chunk)

    def _cleanup(self):
        """Cleanup resources"""
        print("\n[CLEAN] Cleaning up...")
        self.stop.set()

        # Wait for stream thread
        if hasattr(self, 'stream_thread'):
            self.stream_thread.join(timeout=5.0)

        # Logout and close
        try:
            self.xapiLib.logout()
            self.xapiLib.close_channel()
            print("[OK] Cleanup completed")
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}")

        # Final statistics
        if self.start_time:
            total_runtime = (time.time() - self.start_time) / 3600
            print(f"\n[LEVEL2] Final Statistics:")
            print(f"   Total runtime: {total_runtime:.2f} hours")
            print(f"   Total cycles: {self.total_cycles}")
            print(f"   Total messages: {self.total_messages_received}")
            print(f"   Avg messages/hour: {self.total_messages_received / total_runtime if total_runtime > 0 else 0:.1f}")


def main():
    """Main entry point with command-line argument support"""
    parser = argparse.ArgumentParser(
        description='Continuous/Long-Running StreamMarketData Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run infinitely until Ctrl+C
  python streamMarketDataBidirectional_continuous.py --mode infinite

  # Run for 8 hours with 5-minute cycles
  python streamMarketDataBidirectional_continuous.py --mode timed --hours 8 --cycle-delay 300

  # Run for 12 hours with 10-minute cycles, no symbol rotation
  python streamMarketDataBidirectional_continuous.py --mode timed --hours 12 --cycle-delay 600 --no-rotate

  # Run infinitely with 2-minute statistics logging
  python streamMarketDataBidirectional_continuous.py --mode infinite --cycle-delay 120
        """
    )

    parser.add_argument('--mode',
                       choices=['infinite', 'timed'],
                       default='infinite',
                       help='Run mode: infinite (until Ctrl+C) or timed (for specified hours)')

    parser.add_argument('--hours',
                       type=float,
                       default=8.0,
                       help='Total runtime in hours (for timed mode, default: 8.0)')

    parser.add_argument('--cycle-delay',
                       type=int,
                       default=300,
                       help='Delay between cycles in seconds (default: 300 = 5 minutes)')

    parser.add_argument('--no-rotate',
                       action='store_true',
                       help='Disable automatic symbol rotation')

    parser.add_argument('--no-reconnect',
                       action='store_true',
                       help='Disable automatic reconnection on failures')

    args = parser.parse_args()

    # Create client
    client = ContinuousStreamMarketData(enable_reconnection=not args.no_reconnect)

    # Run based on mode
    if args.mode == 'infinite':
        client.run_infinite(
            cycle_delay=args.cycle_delay,
            rotate_symbols=not args.no_rotate
        )
    else:  # timed
        client.run_timed(
            total_hours=args.hours,
            cycle_delay=args.cycle_delay,
            rotate_symbols=not args.no_rotate
        )


if __name__ == "__main__":
    main()
