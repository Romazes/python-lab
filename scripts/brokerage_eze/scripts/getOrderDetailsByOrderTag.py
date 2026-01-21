import order_pb2
import json
from threading import Event
from emsxapilibrary import EMSXAPILibrary


class GetOrderDetailByOrderTag:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.order_tags = [""] #List of Order Tags
        self.event_type = "" #UserSubmitOrder,UserSubmitStagedOrder,UserSubmitCompoundOrder
        # ,UserSubmitChange,UserSubmitCancel,UserSubmitAllocation,UserSubmitAllocationEx,ForeignExecution etc...


    def get_order_detail_by_order_tag(self):
        self.xapiLib.login()
        request = order_pb2.OrderDetailByOrderTagRequest()  # create order detail json request object
        request.UserToken = self.xapiLib.userToken
        request.OrderTags.extend(self.order_tags)
        request.OrderEventType = self.event_type
        response = self.xapiLib.get_order_service_stub().GetOrderDetailByOrderTag(request)  # API call to fetch order detail by id
        print(response)

        self.xapiLib.logout()


if __name__ == "__main__":
    order_search_example = GetOrderDetailByOrderTag()  # password
    order_search_example.get_order_detail_by_order_tag()
