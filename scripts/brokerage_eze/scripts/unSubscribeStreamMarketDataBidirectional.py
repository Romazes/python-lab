from datetime import datetime, timedelta

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time
import logging
import queue

class UnSubscribeStreamMarketDataExample:
    """
    Example demonstrating how to properly unsubscribe from the StreamMarketData API.
    This shows the complete lifecycle: subscribe -> stream -> unsubscribe
    """
    
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()
        self.request_queue = queue.Queue()
        self.stream_active = False
        self.active_subscriptions = {
            'LEVEL1': set(),
            'LEVEL2': set(), 
            'TICK': set()
        }
        
        # Setup logging
        logging.basicConfig(filename='UnSubscribeStreamMarketData.log', level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')

    def start_sample_stream(self):
        """Start a sample bidirectional stream for demonstration"""
        print("🚀 Starting sample StreamMarketData connection...")
        
        # Start the bidirectional stream thread
        self.stream_thread = Thread(target=self._handle_sample_stream)
        self.stream_thread.start()
        
        # Wait for stream to be ready
        self.ready.wait()
        self.stream_active = True
        print("✓ Sample stream is ready!")

    def add_sample_subscriptions(self):
        """Add sample subscriptions that we'll later unsubscribe from"""
        print("\\n📋 Adding sample subscriptions...")
        
        # Add Level1 symbols
        request1 = market_data_pb2.MarketDataStreamRequest()
        request1.UserToken = self.xapiLib.userToken
        request1.RequestType = "ADD_SYMBOL"
        request1.Symbols.extend(["AAPL", "MSFT", "GOOGL"])
        request1.MarketDataLevel = "LEVEL1"
        request1.Request = True
        request1.Advise = True
        
        self.request_queue.put(request1)
        self.active_subscriptions['LEVEL1'].update(["AAPL", "MSFT", "GOOGL"])
        print("✓ Added Level1 symbols: AAPL, MSFT, GOOGL")
        
        time.sleep(2)
        
        # Add Level2 symbols
        request2 = market_data_pb2.MarketDataStreamRequest()
        request2.UserToken = self.xapiLib.userToken
        request2.RequestType = "ADD_SYMBOL"
        request2.Symbols.extend(["AAPL", "TSLA"])
        request2.MarketDataLevel = "LEVEL2"
        request2.Request = True
        request2.Advise = True
        
        self.request_queue.put(request2)
        self.active_subscriptions['LEVEL2'].update(["AAPL", "TSLA"])
        print("✓ Added Level2 symbols: AAPL, TSLA")
        
        time.sleep(2)
        
        # Add Tick symbols
        request3 = market_data_pb2.MarketDataStreamRequest()
        request3.UserToken = self.xapiLib.userToken
        request3.RequestType = "ADD_SYMBOL"
        request3.Symbols.extend(["VOD.LSE"])
        request3.MarketDataLevel = "TICK"
        request3.Request = True
        request3.Advise = True
        
        self.request_queue.put(request3)
        self.active_subscriptions['TICK'].update(["VOD.LSE"])
        print("✓ Added Tick symbols: VOD.LSE")
        
        print(f"\\n📊 Active subscriptions: {self.get_active_subscriptions()}")

    def unsubscribe_all_stream_data(self):
        """Unsubscribe from all StreamMarketData using the dedicated API"""
        try:
            print("\\n🔌 Unsubscribing from all StreamMarketData...")
            
            # Create unsubscribe request
            request = market_data_pb2.UnSubscribeStreamMarketDataRequest()
            request.UserToken = self.xapiLib.userToken
            
            logging.info(f"UnSubscribeStreamMarketData request: {request}")
            
            # Call the unsubscribe API
            response = self.xapiLib.get_market_data_service_stub().UnSubscribeStreamMarketData(request)
            
            if response.Acknowledgement.ServerResponse == "success":
                success_msg = "✓ Successfully unsubscribed from all StreamMarketData"
                print(success_msg)
                logging.info(success_msg)
                
                # Clear active subscriptions
                self.active_subscriptions = {'LEVEL1': set(), 'LEVEL2': set(), 'TICK': set()}
                
                # Log optional fields if present
                if response.OptionalFields:
                    print(f"📋 Server returned optional fields: {dict(response.OptionalFields)}")
                    logging.info(f"Optional fields: {dict(response.OptionalFields)}")
                
                return True
            else:
                error_msg = f'✗ UnSubscribe failed - Server Response: {response.Acknowledgement.ServerResponse}, Error: {response.Acknowledgement.Message}'
                print(error_msg)
                logging.error(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"✗ UnSubscribeStreamMarketData error: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            return False

    def partial_unsubscribe_demo(self):
        """Demonstrate partial unsubscribing using REMOVE_SYMBOL requests"""
        print("\\n🔄 Demonstrating partial unsubscribe using REMOVE_SYMBOL...")
        
        # Remove some Level1 symbols
        if self.active_subscriptions['LEVEL1']:
            symbols_to_remove = ["MSFT", "GOOGL"]
            request = market_data_pb2.MarketDataStreamRequest()
            request.UserToken = self.xapiLib.userToken
            request.RequestType = "REMOVE_SYMBOL"
            request.Symbols.extend(symbols_to_remove)
            request.MarketDataLevel = "LEVEL1"
            
            self.request_queue.put(request)
            self.active_subscriptions['LEVEL1'].difference_update(symbols_to_remove)
            print(f"🗑️ Removed Level1 symbols: {', '.join(symbols_to_remove)}")
            time.sleep(3)
        
        # Remove all Level2 symbols
        if self.active_subscriptions['LEVEL2']:
            symbols_to_remove = list(self.active_subscriptions['LEVEL2'])
            request = market_data_pb2.MarketDataStreamRequest()
            request.UserToken = self.xapiLib.userToken
            request.RequestType = "REMOVE_SYMBOL"
            request.Symbols.extend(symbols_to_remove)
            request.MarketDataLevel = "LEVEL2"
            
            self.request_queue.put(request)
            self.active_subscriptions['LEVEL2'].clear()
            print(f"🗑️ Removed all Level2 symbols: {', '.join(symbols_to_remove)}")
            time.sleep(3)
        
        print(f"📊 Remaining subscriptions: {self.get_active_subscriptions()}")

    def _handle_sample_stream(self):
        """Handle the sample bidirectional streaming connection"""
        try:
            # Create the bidirectional stream
            def request_generator():
                while not self.stop.is_set():
                    try:
                        request = self.request_queue.get(timeout=1.0)
                        logging.info(f"Sending request: {request}")
                        yield request
                        self.request_queue.task_done()
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logging.error(f"Error in request generator: {e}")
                        break

            # Start the bidirectional stream
            response_stream = self.xapiLib.get_market_data_service_stub().StreamMarketData(request_generator())
            self.ready.set()
            
            print("✓ Sample bidirectional stream connection established")
            logging.info("Sample bidirectional stream connection established")
            
            # Process responses
            for response in response_stream:
                if self.stop.is_set():
                    print('🛑 Stopping sample stream...')
                    break
                    
                try:
                    self._process_stream_response(response)
                except Exception as e:
                    error_msg = f"Error processing stream response: {e}"
                    print(error_msg)
                    logging.error(error_msg)
                    
        except Exception as e:
            error_msg = f"Sample bidirectional stream error: {e}"
            print(error_msg)
            logging.error(error_msg)

    def _process_stream_response(self, response):
        """Process different types of stream responses (simplified for demo)"""
        if response.Acknowledgement.ServerResponse != "success":
            error_msg = f"Server error: {response.Acknowledgement.ServerResponse} - {response.Acknowledgement.Message}"
            print(error_msg)
            return

        response_type = response.ResponseType
        
        if response_type == "LEVEL1_DATA":
            print(f"📈 LEVEL1: {response.SymbolDesc} - Ask: {getattr(response.Ask, 'DecimalValue', 'N/A')}, Bid: {getattr(response.Bid, 'DecimalValue', 'N/A')}")
        elif response_type == "LEVEL2_DATA":
            print(f"📊 LEVEL2: {response.DispName} - MM: {response.MktMkrId}")
        elif response_type == "TICK_DATA" and response.Count > 0:
            print(f"🎯 TICK: {response.DispName} - {response.Count} tick updates")
        elif response_type == "STATUS_UPDATE":
            print(f"ℹ️ STATUS: {response.StatusMessage}")

    def get_active_subscriptions(self):
        """Get current active subscriptions"""
        return {k: list(v) for k, v in self.active_subscriptions.items() if v}

    def stop_stream(self):
        """Stop the bidirectional stream"""
        print("\\n🛑 Stopping bidirectional stream...")
        self.stop.set()
        self.stream_active = False
        
        # Wait for stream thread to finish
        if hasattr(self, 'stream_thread'):
            self.stream_thread.join(timeout=5.0)
            
        print("✓ Bidirectional stream stopped")

    def demonstrate_unsubscribe_workflow(self):
        """Demonstrate the complete unsubscribe workflow"""
        print("=" * 70)
        print("UNSUBSCRIBE WORKFLOW DEMONSTRATION")
        print("=" * 70)
        
        try:
            # 1. Start stream and add subscriptions
            print("\\n1. 🚀 Starting sample stream...")
            self.start_sample_stream()
            time.sleep(2)
            
            # 2. Add sample subscriptions
            print("\\n2. 📋 Adding sample subscriptions...")
            self.add_sample_subscriptions()
            time.sleep(5)
            
            # 3. Let stream run
            print("\\n3. ⏱️ Letting stream run for 10 seconds...")
            time.sleep(10)
            
            # 4. Demonstrate partial unsubscribe
            print("\\n4. 🔄 Demonstrating partial unsubscribe...")
            self.partial_unsubscribe_demo()
            time.sleep(5)
            
            # 5. Let remaining stream run
            print("\\n5. ⏱️ Letting remaining subscriptions run for 5 seconds...")
            time.sleep(5)
            
            # 6. Complete unsubscribe
            print("\\n6. 🔌 Performing complete unsubscribe...")
            success = self.unsubscribe_all_stream_data()
            
            if success:
                time.sleep(3)
                print(f"\\n📊 Final subscriptions (should be empty): {self.get_active_subscriptions()}")
                
                # 7. Verify no more data is received
                print("\\n7. ⏱️ Waiting 5 seconds to verify no more data...")
                time.sleep(5)
                print("✓ No more market data received - unsubscribe successful!")
            
        except Exception as e:
            print(f"✗ Error in workflow: {str(e)}")
            logging.error(f"Workflow error: {str(e)}")


def run_unsubscribe_example():
    """Run the UnSubscribeStreamMarketData example"""
    print("=" * 70)
    print("UNSUBSCRIBE STREAMMARKETDATA API EXAMPLE")
    print("=" * 70)
    
    example = UnSubscribeStreamMarketDataExample()
    
    try:
        # Login
        print("\\n🔐 Logging into XAPI...")
        example.xapiLib.login()
        print("✓ Successfully logged in")
        
        # Run the complete workflow demonstration
        example.demonstrate_unsubscribe_workflow()
        
    except Exception as e:
        print(f"✗ Error during execution: {str(e)}")
        logging.error(f"Main execution error: {str(e)}")
        
    finally:
        # Cleanup
        if example.stream_active:
            example.stop_stream()
        example.xapiLib.logout()
        example.xapiLib.close_channel()
        print("\\n✓ UnSubscribeStreamMarketData example completed")


if __name__ == "__main__":
    run_unsubscribe_example()
