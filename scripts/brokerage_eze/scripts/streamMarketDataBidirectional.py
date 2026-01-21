from datetime import datetime, timedelta

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time
import logging
import queue
import os

class StreamMarketDataExample:
    """
    Example demonstrating the bidirectional StreamMarketData API.
    This API allows dynamic subscription management for Level1, Level2, and Tick data
    through a single bidirectional stream.
    """
    
    def __init__(self):
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
        
        # Setup structured logging with proper configuration
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure comprehensive logging for the StreamMarketData bidirectional client"""
        # Create logger with module name
        self.logger = logging.getLogger(__name__)

        # Prevent duplicate handlers if logger already exists
        if self.logger.handlers:
            return

        # Set logging level (can be configured via environment variable)
        log_level = os.getenv('STREAM_LOG_LEVEL', 'INFO').upper()
        numeric_level = getattr(logging, log_level, logging.INFO)
        self.logger.setLevel(numeric_level)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

        # File handler for detailed logging
        file_handler = logging.FileHandler('StreamMarketData_Bidirectional.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler for important messages only
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(simple_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log initial setup
        self.logger.info("StreamMarketData bidirectional client logging initialized")
        self.logger.debug(f"Log level set to: {log_level}")

    def _log_connection_event(self, event_type, details=None):
        """Log connection-related events with structured information"""
        if event_type is None:
            event_type = "Unknown"
        
        context = {
            'event_type': event_type,
            'user_token': self.xapiLib.userToken[:8] + '...' if self.xapiLib.userToken else 'None',
            'active_subscriptions': {
                level: len(symbols) for level, symbols in self.active_subscriptions.items()
            }
        }

        if details:
            if isinstance(details, dict):
                context.update(details)
            else:
                context['status'] = details

        self.logger.info(f"Connection event: {event_type}", extra={'context': context})

    def _log_performance_metric(self, operation, duration, details=None):
        """Log performance metrics for monitoring"""
        context = {
            'operation': operation,
            'duration_ms': duration * 1000 if isinstance(duration, (int, float)) else 0,
            'timestamp': datetime.now().isoformat()
        }

        if details:
            if isinstance(details, dict):
                context.update(details)
            else:
                context['details'] = details

        self.logger.info(f"Performance: {operation} completed in {duration:.3f}s" if isinstance(duration, (int, float)) else f"Data: {operation} for {duration}", extra={'context': context})

    def _log_subscription_change(self, action, symbol, level, details=None):
        """Log subscription changes with context"""
        context = {
            'action': action,
            'symbol': symbol,
            'level': level,
            'total_subscriptions': sum(len(symbols) for symbols in self.active_subscriptions.values())
        }

        if details:
            context.update(details)

        self.logger.info(f"Subscription {action}: {symbol} ({level})", extra={'context': context})

    def _log_error_with_context(self, error, operation, details=None):
        """Log errors with comprehensive context for debugging"""
        context = {
            'operation': operation,
            'error_type': type(error).__name__,
            'active_subscriptions': {
                level: len(symbols) for level, symbols in self.active_subscriptions.items()
            },
            'stream_ready': self.ready.is_set(),
            'stream_stopping': self.stop.is_set()
        }

        if details:
            context.update(details)

        self.logger.error(f"Error in {operation}: {error}", extra={'context': context}, exc_info=True)

    def _log_market_data(self, data_type, symbol, data):
        """Log actual market data received with comprehensive details"""
        # Format the market data for logging
        if data_type == "LEVEL1":
            log_message = f"Market Data [LEVEL1]: {symbol} - Ask: {data.get('ask', 'N/A')}, Bid: {data.get('bid', 'N/A')}, Last: {data.get('last', 'N/A')}, Vol: {data.get('volume', 'N/A')}, High: {data.get('high', 'N/A')}, Low: {data.get('low', 'N/A')}, Chg: {data.get('change', 'N/A')}"
        elif data_type == "LEVEL2":
            log_message = f"Market Data [LEVEL2]: {symbol} - MM: {data.get('market_maker', 'N/A')}, Bid: {data.get('bid', 'N/A')}/{data.get('bid_size', 'N/A')}, Ask: {data.get('ask', 'N/A')}/{data.get('ask_size', 'N/A')}, Cond: {data.get('condition', 'N/A')}"
        elif data_type == "TICK":
            ticks_info = data.get('ticks', [])
            if ticks_info:
                first_tick = ticks_info[0] if isinstance(ticks_info, list) and ticks_info else {}
                log_message = f"Market Data [TICK]: {symbol} - Count: {data.get('tick_count', 0)}, Sample: {first_tick.get('tick_type', 'N/A')}@{first_tick.get('price', 'N/A')}x{first_tick.get('volume', 'N/A')}"
            else:
                log_message = f"Market Data [TICK]: {symbol} - Count: {data.get('tick_count', 0)}"
        else:
            log_message = f"Market Data [{data_type}]: {symbol}"
        
        context = {
            'data_type': data_type,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Log the actual market data with full details
        self.logger.info(log_message, extra={'context': context})

    def start_bidirectional_stream(self):
        """Start the bidirectional streaming connection"""
        self._log_connection_event("Starting bidirectional StreamMarketData connection", "START")
        
        # Validate userToken before starting stream
        if self.xapiLib.userToken is None:
            raise ValueError("UserToken is None - authentication required before starting bidirectional stream")
        if not isinstance(self.xapiLib.userToken, str) or self.xapiLib.userToken.strip() == "":
            raise ValueError("UserToken is empty or invalid - authentication required before starting bidirectional stream")
        
        # Start the bidirectional stream thread
        self.stream_thread = Thread(target=self._handle_bidirectional_stream)
        self.stream_thread.start()
        
        # Wait for stream to be ready
        if not self.ready.wait(timeout=10.0):
            raise TimeoutError("Timeout waiting for bidirectional stream to initialize")
        self._log_connection_event("Bidirectional stream is ready", "READY")

    def add_level1_symbols(self, symbols):
        """Add symbols for Level1 market data"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = "LEVEL1"
        request.Request = True  # Get current snapshot
        request.Advise = True   # Get real-time updates
        
        self.request_queue.put(request)
        self.active_subscriptions['LEVEL1'].update(symbols)
        
        self._log_subscription_change("LEVEL1", symbols, "ADD")

    def add_level2_symbols(self, symbols, market_sources=None):
        """Add symbols for Level2 market data"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "ADD_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = "LEVEL2"
        if market_sources:
            request.MarketSource.extend(market_sources)
        request.Request = True
        request.Advise = True
        
        self.request_queue.put(request)
        self.active_subscriptions['LEVEL2'].update(symbols)
        
        self._log_subscription_change("LEVEL2", symbols, "ADD")

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
        
        self._log_subscription_change("TICK", symbols, "ADD")

    def remove_symbols(self, symbols, market_data_level):
        """Remove symbols from subscription"""
        request = market_data_pb2.MarketDataStreamRequest()
        request.UserToken = self.xapiLib.userToken
        request.RequestType = "REMOVE_SYMBOL"
        request.Symbols.extend(symbols)
        request.MarketDataLevel = market_data_level
        
        self.request_queue.put(request)
        
        if market_data_level in self.active_subscriptions:
            self.active_subscriptions[market_data_level].difference_update(symbols)
        
        self._log_subscription_change(market_data_level, symbols, "REMOVE")

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
        
        self._log_subscription_change(market_data_level, new_symbols, "CHANGE")

    def _handle_bidirectional_stream(self):
        """Handle the bidirectional streaming connection with comprehensive error handling"""
        max_retry_attempts = 3
        retry_delay = 5  # seconds
        attempt = 0

        while attempt < max_retry_attempts and not self.stop.is_set():
            attempt += 1
            try:
                self.logger.info(f"Starting bidirectional stream attempt {attempt}/{max_retry_attempts}")

                # Create the bidirectional stream
                def request_generator():
                    try:
                        # CRITICAL: Send initial authentication request first
                        initial_request = market_data_pb2.MarketDataStreamRequest()
                        initial_request.UserToken = self.xapiLib.userToken
                        initial_request.RequestType = "INIT"  # Initial connection request
                        self.logger.info(f"Sending initial authentication request with UserToken: '{initial_request.UserToken}'")
                        print(f"[DEBUG] Debug - Sending initial request with UserToken: '{initial_request.UserToken}'")
                        yield initial_request

                        # Mark stream as ready after initial request sent
                        self.ready.set()

                        # Now process subsequent requests from the queue
                        while not self.stop.is_set():
                            try:
                                # Get request from queue with timeout
                                request = self.request_queue.get(timeout=1.0)
                                self.logger.info(f"Sending request: {request}")
                                yield request
                                self.request_queue.task_done()
                            except queue.Empty:
                                continue
                            except Exception as e:
                                self.logger.error(f"Error in request generator: {e}")
                                break
                    except Exception as e:
                        self.logger.error(f"Critical error in request generator: {e}")
                        raise

                # Start the bidirectional stream with timeout
                try:
                    response_stream = self.xapiLib.get_market_data_service_stub().StreamMarketData(request_generator())
                    self._log_connection_event("Bidirectional stream connection established", "CONNECTED")
                except Exception as e:
                    self._log_error_with_context(f"Failed to establish bidirectional stream connection: {e}", "CONNECTION_FAILED", {"attempt": attempt, "max_attempts": max_retry_attempts})
                    if attempt < max_retry_attempts:
                        self._log_connection_event(f"Retrying in {retry_delay} seconds", "RETRY")
                        time.sleep(retry_delay)
                    continue

                # Process responses with comprehensive error handling
                try:
                    for response in response_stream:
                        if self.stop.is_set():
                            self._log_connection_event("Stopping bidirectional stream", "STOP")
                            break

                        try:
                            self._process_stream_response(response)
                        except Exception as e:
                            self._log_error_with_context(f"Error processing individual stream response: {e}", "RESPONSE_PROCESSING_ERROR", {"response_type": getattr(response, 'ResponseType', 'UNKNOWN')})
                            # Continue processing other responses even if one fails
                            continue

                except ConnectionError as e:
                    self._log_error_with_context(f"Connection error during response stream iteration: {e}", "CONNECTION_ERROR", {"attempt": attempt, "max_attempts": max_retry_attempts})
                    if attempt < max_retry_attempts and not self.stop.is_set():
                        self._log_connection_event(f"Connection lost, retrying in {retry_delay} seconds", "RETRY")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
                except TimeoutError as e:
                    self._log_error_with_context(f"Timeout error during response stream iteration: {e}", "TIMEOUT_ERROR", {"attempt": attempt, "max_attempts": max_retry_attempts})
                    if attempt < max_retry_attempts and not self.stop.is_set():
                        self._log_connection_event(f"Timeout occurred, retrying in {retry_delay} seconds", "RETRY")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise
                except Exception as e:
                    self._log_error_with_context(f"Unexpected error during response stream iteration: {e}", "STREAM_ERROR", {"attempt": attempt, "max_attempts": max_retry_attempts})
                    if attempt < max_retry_attempts and not self.stop.is_set():
                        self._log_connection_event(f"Stream error occurred, retrying in {retry_delay} seconds", "RETRY")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise

                # If we reach here successfully, break out of retry loop
                break

            except Exception as e:
                error_msg = f"Bidirectional stream error on attempt {attempt}: {e}"
                print(f"[CRITICAL] {error_msg}")
                self.logger.error(error_msg, exc_info=True)

                if attempt >= max_retry_attempts:
                    self.logger.error(f"Max retry attempts ({max_retry_attempts}) exceeded, giving up")
                    raise
                elif not self.stop.is_set():
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)

    def _process_stream_response(self, response):
        """Process different types of stream responses"""
        # Log acknowledgment details
        if hasattr(response, 'Acknowledgement') and response.Acknowledgement.ServerResponse:
            ack_msg = f"ACK [SERVER] {response.Acknowledgement.ServerResponse}: {response.Acknowledgement.Message}"
            print(ack_msg)
            
        if response.Acknowledgement.ServerResponse != "success":
            self._log_error_with_context(f"Server error: {response.Acknowledgement.ServerResponse} - {response.Acknowledgement.Message}", "SERVER_ERROR", {"server_response": response.Acknowledgement.ServerResponse})
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
        elif response_type == "HEARTBEAT":
            self._process_heartbeat(response)
        elif response_type == "CONNECTION_STATUS":
            self._process_connection_status(response)
        else:
            # Log unknown response types with more details
            unknown_msg = f"UNKNOWN [RESPONSE] Type: {response_type}, Symbol: {getattr(response, 'DispName', 'N/A')}, Count: {getattr(response, 'Count', 'N/A')}"
            print(unknown_msg)
            self._log_error_with_context(f"Unknown response type: {response_type}", "UNKNOWN_RESPONSE_TYPE", {"response_type": response_type})

    def _is_meaningful_level1_update(self, response):
        """Check if Level1 update contains meaningful data (not just a heartbeat)
        
        Args:
            response: MarketDataStreamResponse with Level1 data
            
        Returns:
            bool: True if update has meaningful data, False if it's a heartbeat
        """
        ask_val = response.Ask.DecimalValue if response.Ask and not response.Ask.Isnull else 0
        bid_val = response.Bid.DecimalValue if response.Bid and not response.Bid.Isnull else 0
        last_val = response.Trdprc1.DecimalValue if response.Trdprc1 and not response.Trdprc1.Isnull else 0
        
        # Consider meaningful if any price is non-zero OR symbol has a description
        return not (ask_val == 0 and bid_val == 0 and last_val == 0 and not response.SymbolDesc)
    
    def _process_level1_data(self, response):
        """Process Level1 market data"""
        # Filter out empty/meaningless updates (heartbeats with no data)
        if not self._is_meaningful_level1_update(response):
            return
        
        symbol = response.SymbolDesc if response.SymbolDesc else response.DispName
        ask_val = response.Ask.DecimalValue if response.Ask and not response.Ask.Isnull else 0
        bid_val = response.Bid.DecimalValue if response.Bid and not response.Bid.Isnull else 0
        last_val = response.Trdprc1.DecimalValue if response.Trdprc1 and not response.Trdprc1.Isnull else 0
        
        # Log the actual market data
        market_data = {
            "symbol": symbol,
            "ask": ask_val,
            "bid": bid_val,
            "last": last_val,
            "ask_size": getattr(getattr(response, 'Asksize', None), 'value', 0) if hasattr(response, 'Asksize') and getattr(response, 'Asksize', None) else 0,
            "bid_size": getattr(getattr(response, 'Bidsize', None), 'value', 0) if hasattr(response, 'Bidsize') and getattr(response, 'Bidsize', None) else 0,
            "volume": getattr(getattr(response, 'Acvol1', None), 'value', 0) if hasattr(response, 'Acvol1') and getattr(response, 'Acvol1', None) else 0,
            "high": getattr(getattr(response, 'High', None), 'DecimalValue', 0) if hasattr(response, 'High') and getattr(response, 'High', None) and not getattr(getattr(response, 'High', None), 'Isnull', True) else 0,
            "low": getattr(getattr(response, 'Low', None), 'DecimalValue', 0) if hasattr(response, 'Low') and getattr(response, 'Low', None) and not getattr(getattr(response, 'Low', None), 'Isnull', True) else 0,
            "open": getattr(getattr(response, 'Open', None), 'DecimalValue', 0) if hasattr(response, 'Open') and getattr(response, 'Open', None) and not getattr(getattr(response, 'Open', None), 'Isnull', True) else 0,
            "change": getattr(getattr(response, 'NetChg1', None), 'DecimalValue', 0) if hasattr(response, 'NetChg1') and getattr(response, 'NetChg1', None) and not getattr(getattr(response, 'NetChg1', None), 'Isnull', True) else 0,
            "change_percent": getattr(getattr(response, 'PctChg', None), 'DecimalValue', 0) if hasattr(response, 'PctChg') and getattr(response, 'PctChg', None) and not getattr(getattr(response, 'PctChg', None), 'Isnull', True) else 0
        }
        
        self._log_market_data("LEVEL1", symbol, market_data)
        
        # Print actual market data values to console
        volume = getattr(getattr(response, 'Acvol1', None), 'value', 0) if hasattr(response, 'Acvol1') and getattr(response, 'Acvol1', None) else 0
        high = getattr(getattr(response, 'High', None), 'DecimalValue', 0) if hasattr(response, 'High') and getattr(response, 'High', None) and not getattr(getattr(response, 'High', None), 'Isnull', True) else 0
        low = getattr(getattr(response, 'Low', None), 'DecimalValue', 0) if hasattr(response, 'Low') and getattr(response, 'Low', None) and not getattr(getattr(response, 'Low', None), 'Isnull', True) else 0
        change = getattr(getattr(response, 'NetChg1', None), 'DecimalValue', 0) if hasattr(response, 'NetChg1') and getattr(response, 'NetChg1', None) and not getattr(getattr(response, 'NetChg1', None), 'Isnull', True) else 0
        
        message = "LEVEL1 [{}] Symbol: {}, Ask: {}, Bid: {}, Last: {}, Vol: {}, High: {}, Low: {}, Chg: {}".format(
            symbol,
            symbol,
            ask_val if ask_val != 0 else "N/A",
            bid_val if bid_val != 0 else "N/A", 
            last_val if last_val != 0 else "N/A",
            volume if volume != 0 else "N/A",
            high if high != 0 else "N/A",
            low if low != 0 else "N/A",
            change if change != 0 else "N/A"
        )
        print(message)
        
        self._log_performance_metric("LEVEL1", symbol, {
            "ask": ask_val,
            "bid": bid_val,
            "last": last_val
        })

    def _is_meaningful_level2_update(self, response):
        """Check if Level2 update contains meaningful data (not just a heartbeat)
        
        Args:
            response: MarketDataStreamResponse with Level2 data
            
        Returns:
            bool: True if update has meaningful data, False if it's a heartbeat
        """
        bid_val = response.MktMkrBid.DecimalValue if response.MktMkrBid and not response.MktMkrBid.Isnull else 0
        ask_val = response.MktMkrAsk.DecimalValue if response.MktMkrAsk and not response.MktMkrAsk.Isnull else 0
        bid_size = response.MktMkrBidsize.value if response.MktMkrBidsize else 0
        ask_size = response.MktMkrAsksize.value if response.MktMkrAsksize else 0
        
        # Consider meaningful if any value is non-zero
        return not (bid_val == 0 and ask_val == 0 and bid_size == 0 and ask_size == 0)
    
    def _process_level2_data(self, response):
        """Process Level2 market data"""
        # Filter out empty/meaningless updates (heartbeats with no meaningful data)
        if not self._is_meaningful_level2_update(response):
            return
        
        bid_val = response.MktMkrBid.DecimalValue if response.MktMkrBid and not response.MktMkrBid.Isnull else 0
        ask_val = response.MktMkrAsk.DecimalValue if response.MktMkrAsk and not response.MktMkrAsk.Isnull else 0
        bid_size = response.MktMkrBidsize.value if response.MktMkrBidsize else 0
        ask_size = response.MktMkrAsksize.value if response.MktMkrAsksize else 0
        
        # Skip logging if all values are zero (heartbeat/placeholder)
        if bid_val == 0 and ask_val == 0 and bid_size == 0 and ask_size == 0:
            return
        
        symbol = response.DispName
        market_maker = response.MktMkrId
        
        # Log the actual market data
        market_data = {
            "symbol": symbol,
            "market_maker": market_maker,
            "bid": bid_val,
            "ask": ask_val,
            "bid_size": bid_size,
            "ask_size": ask_size,
            "bid_time": getattr(response, 'MktMkrBidTime', None),
            "ask_time": getattr(response, 'MktMkrAskTime', None),
            "condition": getattr(response, 'Condition', None)
        }
        
        self._log_market_data("LEVEL2", symbol, market_data)
        
        # Print actual market data values to console
        condition = getattr(response, 'Condition', None)
        bid_time = getattr(response, 'MktMkrBidTime', None)
        ask_time = getattr(response, 'MktMkrAskTime', None)
        
        message = "LEVEL2 [{}] Symbol: {}, MM: {}, Bid: {}/{}, Ask: {}/{}, Cond: {}, Times: {}/{}".format(
            symbol,
            symbol,
            market_maker,
            bid_val if bid_val != 0 else "N/A",
            bid_size if bid_size != 0 else "N/A",
            ask_val if ask_val != 0 else "N/A", 
            ask_size if ask_size != 0 else "N/A",
            condition or "N/A",
            bid_time or "N/A",
            ask_time or "N/A"
        )
        print(message)
        
        self._log_performance_metric("LEVEL2", symbol, {
            "market_maker": market_maker,
            "bid": bid_val,
            "ask": ask_val,
            "bid_size": bid_size,
            "ask_size": ask_size
        })

    def _get_tick_type_name(self, tick_type_value):
        """Get human-readable tick type name"""
        tick_types = {0: "TRADE", 1: "BID", 2: "ASK", 3: "REGIONAL_BID", 4: "REGIONAL_ASK"}
        return tick_types.get(tick_type_value, f"UNKNOWN({tick_type_value})")

    def _format_tick_price(self, price_obj):
        """Format tick price safely"""
        return price_obj.DecimalValue if price_obj and not price_obj.Isnull else "N/A"

    def _format_tick_volume(self, volume_list, index):
        """Format tick volume safely"""
        return volume_list[index] if index < len(volume_list) else "N/A"

    def _log_tick_message(self, symbol, tick_type, price, volume):
        """Log individual tick message"""
        # Print actual tick data values to console with more details
        message = "TICK [{}] Symbol: {}, Type: {}, Price: {}, Volume: {}".format(
            symbol or "UNKNOWN", 
            symbol or "UNKNOWN", 
            tick_type, 
            price, 
            volume
        )
        print(message)
        
        self._log_performance_metric("TICK", symbol, {
            "tick_type": tick_type,
            "price": price,
            "volume": volume
        })

    def _log_remaining_ticks_summary(self, remaining_count, symbol):
        """Log summary of remaining ticks"""
        if remaining_count > 0:
            # Print summary to console
            summary_msg = f"TICK [BATCH] ... and {remaining_count} more tick(s) for {symbol}"
            print(summary_msg)
            
            self._log_performance_metric("TICK_BATCH", symbol, {
                "remaining_ticks": remaining_count,
                "action": "truncated_display"
            })

    def _process_tick_data(self, response):
        """Process Tick data with reduced cognitive complexity"""
        if response.Count <= 0:
            return

        max_ticks_to_log = 10
        ticks_logged = 0
        symbol_name = response.DispName or "UNKNOWN"
        
        # Collect all tick data for comprehensive logging
        all_ticks = []
        
        # Process ticks up to the limit
        for i in range(min(len(response.TrdPrc1List), response.Count)):
            if ticks_logged >= max_ticks_to_log:
                remaining = response.Count - ticks_logged
                self._log_remaining_ticks_summary(remaining, symbol_name)
                break

            # Extract and format tick data
            tick_type = self._get_tick_type_name(response.TickTypeList[i])
            price = self._format_tick_price(response.TrdPrc1List[i])
            volume = self._format_tick_volume(response.TrdVol1List, i)
            
            # Get tick time safely
            tick_time = None
            if hasattr(response, 'TickTimeList') and response.TickTimeList and i < len(response.TickTimeList):
                tick_time = response.TickTimeList[i]
            
            tick_data = {
                "tick_type": tick_type,
                "price": price,
                "volume": volume,
                "tick_time": tick_time,
                "tick_size": response.TrdVol1List[i] if i < len(response.TrdVol1List) else 0
            }
            
            all_ticks.append(tick_data)
            
            # Log the tick
            self._log_tick_message(symbol_name, tick_type, price, volume)
            ticks_logged += 1
        
        # Log comprehensive market data for all ticks in this response
        if all_ticks:
            market_data = {
                "symbol": symbol_name,
                "tick_count": len(all_ticks),
                "ticks": all_ticks,
                "total_response_count": response.Count
            }
            
            self._log_market_data("TICK", symbol_name, market_data)

    def _process_status_update(self, response):
        """Process status updates"""
        # Print status update to console
        message = f"STATUS [INFO] {response.StatusMessage}"
        print(message)
        
        self._log_connection_event(response.StatusMessage, "STATUS_UPDATE")

    def _process_heartbeat(self, response):
        """Process heartbeat messages"""
        # Print heartbeat to console (less verbose)
        heartbeat_msg = f"HEARTBEAT [PING] {getattr(response, 'StatusMessage', 'Keep-alive')}"
        print(heartbeat_msg)
        
        self._log_connection_event("Heartbeat received", "HEARTBEAT")

    def _process_connection_status(self, response):
        """Process connection status messages"""
        status = getattr(response, 'StatusMessage', 'Unknown status')
        connection_msg = f"CONNECTION [STATUS] {status}"
        print(connection_msg)
        
        self._log_connection_event(status, "CONNECTION_STATUS")

    def get_active_subscriptions(self):
        """Get current active subscriptions"""
        return {k: list(v) for k, v in self.active_subscriptions.items() if v}

    def stop_stream(self):
        """Stop the bidirectional stream"""
        self._log_connection_event("Stopping bidirectional stream", "STOP")
        self.stop.set()
        
        # Wait for stream thread to finish
        if hasattr(self, 'stream_thread'):
            self.stream_thread.join(timeout=5.0)
            
        self._log_connection_event("Bidirectional stream stopped", "STOPPED")


def run_stream_market_data_example():
    """Run the StreamMarketData bidirectional streaming example"""
    print("=" * 70)
    print("BIDIRECTIONAL STREAMMARKETDATA API EXAMPLE")
    print("=" * 70)
    
    example = StreamMarketDataExample()
    
    try:
        # Login
        print("\\n1. [LOGIN] Logging into XAPI...")
        example.xapiLib.login()
        print("[OK] Successfully logged in")
        
        # Start bidirectional stream
        print("\\n2. [START] Starting bidirectional stream...")
        example.start_bidirectional_stream()
        time.sleep(2)
        
        # Add Level1 symbols
        print("\\n3. [LEVEL1] Adding Level1 symbols...")
        example.add_level1_symbols(["AAPL", "MSFT", "GOOGL"])
        time.sleep(5)
        
        # Add Level2 symbols
        print("\\n4. [LEVEL2] Adding Level2 symbols...")
        example.add_level2_symbols(["AAPL", "TSLA"])
        time.sleep(5)
        
        # Add Tick symbols
        print("\\n5. [TICK] Adding Tick symbols...")
        example.add_tick_symbols(["VOD.LSE"])
        time.sleep(5)
        
        print(f"\\n[CLIPBOARD] Current subscriptions: {example.get_active_subscriptions()}")
        
        # Let all streams run
        print("\\n6. [TIMER] Letting streams run for 15 seconds...")
        time.sleep(15)
        
        # Demonstrate dynamic subscription changes
        print("\\n7. [CHANGE] Changing Level1 subscription...")
        example.change_subscription("LEVEL1", ["NVDA", "AMD"])
        time.sleep(10)
        
        print("\\n8. [REMOVE] Removing some symbols...")
        example.remove_symbols(["TSLA"], "LEVEL2")
        example.remove_symbols(["VOD.LSE"], "TICK")
        time.sleep(5)
        
        print(f"\\n[CLIPBOARD] Final subscriptions: {example.get_active_subscriptions()}")
        
        # Let modified streams run
        print("\\n9. [TIMER] Letting modified streams run for 10 more seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"[ERROR] Error during execution: {str(e)}")
        example._log_error_with_context(f"Main execution error: {str(e)}", "EXECUTION_ERROR", {"phase": "main"})
        
    finally:
        # Cleanup
        example.stop_stream()
        example.xapiLib.logout()
        example.xapiLib.close_channel()
        print("\\n[OK] StreamMarketData example completed successfully")


if __name__ == "__main__":
    run_stream_market_data_example()
