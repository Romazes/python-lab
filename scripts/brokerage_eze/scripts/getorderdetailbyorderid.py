import order_pb2
import json
from threading import Event
from emsxapilibrary import EMSXAPILibrary


class GetOrderDetailByOrderId:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.order_id = "order-id"

    def get_order_detail_by_order_id(self):
        self.xapiLib.login()

        request = order_pb2.OrderDetailByOrderIdRequest()  # create order detail json request object
        request.UserToken = self.xapiLib.userToken
        request.OrderId = self.order_id
        response = self.xapiLib.get_order_service_stub().GetOrderDetailByOrderId(request)  # API call to fetch order detail by id
        print(response)

        self.xapiLib.logout()


if __name__ == "__main__":
    order_search_example = GetOrderDetailByOrderId()  # password
    order_search_example.get_order_detail_by_order_id()
