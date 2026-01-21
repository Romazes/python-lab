from datetime import datetime, timedelta

from emsxapilibrary import EMSXAPILibrary
import market_data_pb2
from threading import Event, Thread
import time

class UnSubscribeTickData:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def un_subscribe_tick_data(self):
        request = market_data_pb2.UnSubscribeTickDataRequest()  # create getTickData request object
        request.UserToken = self.xapiLib.userToken
        response = self.xapiLib.get_market_data_service_stub().UnSubscribeTickData(request) # API call to fetch Level1 market data
        print(response)

if __name__ == "__main__":
    un_subscribe_tick_data_example = UnSubscribeTickData()  # password
    un_subscribe_tick_data_example.xapiLib.login()
    un_subscribe_tick_data_example.un_subscribe_tick_data()
    un_subscribe_tick_data_example.xapiLib.logout()
    un_subscribe_tick_data_example.xapiLib.close_channel()




