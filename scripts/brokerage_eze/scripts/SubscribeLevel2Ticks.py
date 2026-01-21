from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time
import logging


class SubscribeLevel2Ticks:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()
        self.thread = None

    def start_listening(self):
        # Check if a previous thread is still running
        if self.thread is not None and self.thread.is_alive():
            logging.warning('Previous subscription thread is still running. Waiting for it to finish...')
            self.stop.set()
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logging.error('Previous thread did not stop gracefully')
                raise RuntimeError('Cannot start new subscription while previous thread is still active')

        # Reset events for new subscription
        self.ready.clear()
        self.stop.clear()

        # start thread to listen to updates from the server about level 2 ticks
        self.thread = Thread(target=self._subscribe_level2_ticks)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    def _subscribe_level2_ticks(self):
        request = market_data_pb2.Level2MarketDataRequest()  # create Level2 market data request object
        request.UserToken = self.xapiLib.userToken
        request.Symbols.extend(["VOD.LSE", "MSFT", "GOOGL"])  # List of ticker symbols
        request.Advise = True  # Enable real-time streaming updates from the server
        request.Request = True  # Request initial snapshot of current data before streaming begins

        # Set up logging
        logging.basicConfig(filename='SubscribeLevel2Ticks.log', level=logging.INFO, format='%(asctime)s - %(message)s')

        # Log the request
        logging.info("Request: {}".format(request))

        response = self.xapiLib.get_market_data_service_stub().SubscribeLevel2Ticks(request)  # API call to subscribe to Level2 ticks
        self.ready.set()

        for data in response:
            if self.stop.is_set():
                print('time to stop reading responses')
                break
            try:
                if data.Acknowledgement.ServerResponse == "success":
                    # Log and print the data
                    logging.info(data)
                    print(f"DispName: {data.DispName}, "
                          f"MktMkrId: {data.MktMkrId}, "
                          f"MktMkrDisplay: {data.MktMkrDisplay}, "
                          f"Bid: {data.MktMkrBid.DecimalValue if not data.MktMkrBid.Isnull else 'N/A'}, "
                          f"BidSize: {data.MktMkrBidsize}, "
                          f"Ask: {data.MktMkrAsk.DecimalValue if not data.MktMkrAsk.Isnull else 'N/A'}, "
                          f"AskSize: {data.MktMkrAsksize}, "
                          f"Status: {data.MktMkrStatus}, "
                          f"Source: {data.MktSource}, "
                          f"UpdateType: {data.QuoteUpdateType}")
                else:
                    error_msg = 'Server Response: {0}, Error Message: {1}'.format(
                        data.Acknowledgement.ServerResponse,
                        data.Acknowledgement.Message)
                    print(error_msg)
                    logging.error(error_msg)
            except Exception as e:
                print(e)
                logging.error(f"Exception: {e}")
            logging.info("-------------------------------------------------")


if __name__ == "__main__":
    subscribe_level2_ticks_example = SubscribeLevel2Ticks()
    subscribe_level2_ticks_example.xapiLib.login()
    print('User token: ' + subscribe_level2_ticks_example.xapiLib.userToken)
    subscribe_level2_ticks_example.start_listening()
    time.sleep(30)  # Listen for 30 seconds
    subscribe_level2_ticks_example.stop.set()
    subscribe_level2_ticks_example.xapiLib.logout()
    subscribe_level2_ticks_example.xapiLib.close_channel()
