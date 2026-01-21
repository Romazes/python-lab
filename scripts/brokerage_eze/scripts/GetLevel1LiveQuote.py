from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time

class GetLevel1LiveQuote:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about level 1 live quotes
        self.thread = Thread(target=self._get_level1_live_quote)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    def _get_level1_live_quote(self):
        request = market_data_pb2.Level1MarketDataRequest()  # create Level1 market data request object
        request.UserToken = self.xapiLib.userToken
        request.Symbols.extend(["AAPL", "VOD.LSE", "BARC.LSE", "GSK.LSE"])  # List of ticker symbols
        request.Advise = False  # If true, real-time updates from the server will be registered for.
        request.Request = True  # If true, a current snapshot of the data will be retrieved
        response = self.xapiLib.get_market_data_service_stub().SubscribeLevel1Ticks(request)  # API call to subscribe to Level1 live ticks
        self.ready.set()

        for data in response:
            if (self.stop.is_set()):
                print('time to stop reading responses')
                break
            try:
                if data.Acknowledgement.ServerResponse == "success":
                    print(f"DispName: {data.DispName}, SymbolDesc: {data.SymbolDesc}, Bid: {data.Bid.DecimalValue if not data.Bid.Isnull else 'N/A'}, Ask: {data.Ask.DecimalValue if not data.Ask.Isnull else 'N/A'}")
                else:
                    print(f'Server Response: {data.Acknowledgement.ServerResponse} | Message: {data.Acknowledgement.Message}')

            except Exception as e:
                print(e)

if __name__ == "__main__":
    get_level1_live_quote_example = GetLevel1LiveQuote()
    get_level1_live_quote_example.xapiLib.login()
    print('User token: ' + get_level1_live_quote_example.xapiLib.userToken)
    get_level1_live_quote_example.start_listening()
    time.sleep(30)  # Listen for 30 seconds
    get_level1_live_quote_example.stop.set()
    get_level1_live_quote_example.xapiLib.logout()
    get_level1_live_quote_example.xapiLib.close_channel()
