from time import sleep

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2 as mkt
from datetime import datetime
from datetime import timedelta

class GetIntradayBars: # set username, password, domain, locale, port number and server address details
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'M'

    def get_intraday_bars(self):
        self.xapiLib.login()
        request = mkt.IntradayBarsRequest() # create optionsandgreekdatarequest object
        request.Symbol= self.symbol # list of ticker symbols
        request.UserToken = self.xapiLib.userToken
        request.BarInterval = 1 #Bar interval in minutes
        request.DaysBack = 1 #The number of days worth of bars to retrieve
        request.StartAtMidnight = False #If set to True, the first bar of the day includes all data since midnight, otherwise the first bar of the day includes all data since the session open time
        request.ShowPrePostMarket = False  # If set to True, we can get the pre/post hours data, otherwise we will be only getting the market hrs data irrespective of the start and stop time.

        request.Date.FromDatetime(datetime.now())  # The end date for the query, i.e. the most recent date for which Bars should be retrieved.  If null, defaults to the current date.
        request.StartTime.FromTimedelta(timedelta(hours=12, minutes=10,
                                                  seconds=50))  # Bars earlier in the day than this start time will be excluded.  If null, there is no restriction.
        request.StopTime.FromTimedelta(timedelta(hours=20, minutes=30,
                                                 seconds=40))  # Bars later in the day than this stop time will be excluded.  If null, there is no restriction.
        request.requestId.value = 12345  # A user-supplied request ID that can be used to disambiguate response data.  This is ignored by the server but will be echoed back

        response = self.xapiLib.get_market_data_service_stub().GetIntradayBars(request) # API call to fetch options and greek data
        sleep(10)
        if hasattr(response, 'Acknowledgement'):
            print(response.Acknowledgement.ServerResponse) # accessing response object

        self.xapiLib.logout()

if __name__ == "__main__":
    options_and_greek_data_example = GetIntradayBars()  # password
    options_and_greek_data_example.get_intraday_bars()