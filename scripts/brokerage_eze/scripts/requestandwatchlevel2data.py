import market_data_pb2 as mkt
from threading import Event, Thread
import time
from emsxapilibrary import EMSXAPILibrary
from threading import Event

class RequestAndWatchLevel2Data:  # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self.request_and_watch_level2_data)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    def request_and_watch_level2_data(self):
        request = mkt.Level2MarketDataRequest()  # create Level2 market data request object
        request.UserToken = self.xapiLib.userToken
        request.Symbols.extend([r"AAPL"])  # List of ticker symbols
        request.Advise = True  # If true, real-time updates from the server will be registered for.
        request.Request = True  # If true, a current snapshot of the data will be retrieved
        response = self.xapiLib.get_market_data_service_stub().SubscribeLevel2Ticks(request)  # API call to fetch Level2 market data
        self.ready.set()

        for data in response:
            if(self.stop.is_set()):
                print('time to stop reading responses')
                break
            try:
                if data.Acknowledgement.ServerResponse == "success":
                    if not data.MktMkrAsk.Isnull and data.MktMkrAsk.DecimalValue != 0.0:
                        print('DispName:{0} Ask:{1} Market ID: {2} '.format(data.DispName,
                                                                            data.MktMkrAsk.DecimalValue,
                                                                            data.MktMkrId))
                    if not data.MktMkrBid.Isnull and data.MktMkrBid.DecimalValue != 0.0:
                        print('DispName:{0} Bid:{1} Market ID: {2}'.format(data.DispName,
                                                                           data.MktMkrBid.DecimalValue, data.MktMkrId))
                else:
                    print('Server Response: {0} , Error Message : {1}'.format(data.Acknowledgement.ServerResponse,
                                                                              data.Acknowledgement.Message))

            except Exception as e:
                print(e)

if __name__ == "__main__":
    request_and_watch_level2_data_example = RequestAndWatchLevel2Data()  # password
    request_and_watch_level2_data_example.xapiLib.login()
    request_and_watch_level2_data_example.start_listening()
    time.sleep(10)
    request_and_watch_level2_data_example.stop.set()
    request_and_watch_level2_data_example.xapiLib.logout()
    request_and_watch_level2_data_example.xapiLib.close_channel()