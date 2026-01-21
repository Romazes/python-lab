from datetime import datetime, timedelta

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time
import logging
class SubscribeTickData:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.stop = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self._subscribe_tick_data)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    def _subscribe_tick_data(self):
        data = {
            "Symbol": 'VOD.LSE',
            "TickTypes": [{"TickOption": 0}, {"TickOption": 1}, {"TickOption": 2}]
            # TRADE = 0;BID = 1;ASK = 2;REGIONAL_BID = 3;REGIONAL_ASK = 4;DELETED = 11;INSERTED = 12;IRREGULAR_DELETE = 44;FORM_T_TRADE = 32;
        }

        request = market_data_pb2.SubscribeTickDataRequest(**data)  # create getTickData request object
        request.UserToken = self.xapiLib.userToken
        request.Request = True
        request.Date.FromDatetime(
             datetime.now())  # The end date for the query, i.e. the most recent date for which Ticks should be retrieved.  If null, defaults to the current date.
        request.StartTime.FromTimedelta(timedelta(hours=12, minutes=10,
                                                   seconds=50))  # Records earlier in the day than this start time will be excluded.  If null, there is no restriction.
        request.StopTime.FromTimedelta(timedelta(hours=20, minutes=30,
                                                  seconds=40))  # Records later in the day than this stop time will be excluded.  If null, there is no restriction.
        request.RequestId.value = 12345  # A user-suppli  ed request ID that can be used to disambiguate response data.  This is ignored by the server but will be echoed back
        # Set up logging
        logging.basicConfig(filename='SubscribeTickData_Request_Advice_True.log', level=logging.INFO, format='%(message)s')

        # Log the response
        logging.info("Request: {}".format(request))  # Log the request
        response = self.xapiLib.get_market_data_service_stub().SubscribeTickData(request) # API call to fetch Level1 market data
        self.ready.set()


        for data in response:
            if(self.stop.is_set()):
                print('time to stop reading responses')
                break
            try:
                if data.Acknowledgement.ServerResponse == "success":
                    logging.info(data)
                    print(data)
                else:
                    print('Server Response: {0} , Error Message : {1}'.format(data.Acknowledgement.ServerResponse,
                                                                              data.Acknowledgement.Message))
            except Exception as e:
                print(e)
            logging.info("-------------------------------------------------")

if __name__ == "__main__":
    subscribe_tick_data_example = SubscribeTickData()  # password
    subscribe_tick_data_example.xapiLib.login()
    subscribe_tick_data_example.start_listening()
    time.sleep(10000)
    subscribe_tick_data_example.stop.set()
    subscribe_tick_data_example.xapiLib.logout()
    subscribe_tick_data_example.xapiLib.close_channel()




