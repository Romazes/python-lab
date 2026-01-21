import order_pb2
import order_pb2_grpc as ord_grpc
from datetime import datetime
from datetime import timedelta
from emsxapilibrary import EMSXAPILibrary
from threading import Event


class getorderdetailbydaterange:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ord_stub = None
        self.start_year = 2025
        self.start_month = 2
        self.start_day = 10
        self.end_year = 2025
        self.end_month = 2
        self.end_day = 10
        self.start_hour = 0
        self.start_minutes = 0
        self.start_seconds = 0
        self.end_hour = 24
        self.end_minutes = 00
        self.end_seconds = 00
        self.timeout = 100
        self.ready = Event()

    def get_order_detail_by_date_range(self):
        try:
            self.xapiLib.login()

            request = order_pb2.OrderDetailByDateRangeRequest()  # create order detail json request object
            request.UserToken = self.xapiLib.userToken
            request.TimeoutInSeconds = self.timeout
            request.StartDate.FromDatetime(datetime(year=self.start_year, month=self.start_month, day=self.start_day))
            request.EndDate.FromDatetime(datetime(year=self.end_year, month=self.end_month, day=self.end_day))
            # request.StartTime.FromTimedelta(
            #     timedelta(hours=self.start_hour, minutes=self.start_minutes, seconds=self.start_seconds))
            # request.EndTime.FromTimedelta(
            #     timedelta(hours=self.end_hour, minutes=self.end_minutes, seconds=self.end_seconds))
            response = self.xapiLib.get_order_service_stub().GetOrderDetailByDateRange(request)  # API call to fetch order detail by id
            for order_info in response:
                print(order_info.Acknowledgement.ServerResponse)

            self.xapiLib.logout()

        except Exception as e:
            print(e)


if __name__ == "__main__":
    order_search_example = getorderdetailbydaterange()  # password
    order_search_example.get_order_detail_by_date_range()
    