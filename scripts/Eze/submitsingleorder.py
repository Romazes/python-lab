import time
from datetime import datetime
from threading import Event, Thread, Lock
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary

class OrderTimingStore:
    def __init__(self):
        self.submit_times = {}   # order_id -> submit_time
        self.lock = Lock()

timing = OrderTimingStore()


class CreateSingleOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'AAPL'
        self.quantity = 150  # Quantity/volume
        self.side = 'BUY'
        self._staged = False
        self._claim_required = False
        self._expiration = 3  # DAY = 0, GTC = 1, GTX = 2, CLO = 3, OPG = 4, IOC = 5, GTD = 6, OTHER = 7
        self.prc = 120.520
        self.prc_type = 1  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
        self._route = 'DEMOEUR'
        self.order_account = 'TAL;TEST;YGUO;1'
        self.get_order_details = True  # True/False, Returns Order Details when set to True
        self.port = 9000

        self.ready = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self.subscribe_order_info)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    # this is the thread func for the order listener
    def subscribe_order_info(self):

        subscribe_request = ord.SubscribeOrderInfoRequest()
        subscribe_request.ExcludeHistory = True
        subscribe_request.UserToken = self.xapiLib.userToken
        start = time.perf_counter()
        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request) # 1
        self.ready.set()
        
        try:
            for order_info in subscribe_response:
                now = time.perf_counter()
                # message = "OrderId: " + order_info.OrderId \
                #           + " Symbol:" + order_info.Symbol \
                #           + " Type:" + order_info.Type \
                #           + " CurrentStatus:" + order_info.CurrentStatus \
                #           + " Volume:" + str(order_info.Volume) \
                #           + " VolumeTraded:" + str(order_info.VolumeTraded) \
                #           + " Price:" + str(order_info.Price.value) \
                #           + " PriceType:" + order_info.PriceType.PriceTypesEnum.Name(order_info.PriceType.PriceType) \
                #           + " Reason:" + order_info.Reason \
                #           + " TimeStamp:" + str(order_info.TimeStamp) \
                #           + " GoodFrom:" + str(order_info.GoodFrom) \
                #           + " TimeInForce:" + order_info.TimeInForce.ExpirationTypes.Name(
                #     order_info.TimeInForce.Expiration) \
                #           + " StopPrice:" + str(order_info.StopPrice) \
                #           + " UserMessage:" + order_info.UserMessage \
                #           + " ExpirationDate:" + order_info.ExpirationDate.ToJsonString() \
                #           + " Side:" + order_info.Side \
                #           + " Route:" + order_info.Route \
                #           + " Account:" + order_info.Account \
                #           + " OrderTag:" + order_info.OrderTag \
                #           + " TraderId:" + order_info.TraderId \
                #           + " ClaimedByClerk:" + order_info.ClaimedByClerk \
                    # + " LinkedOrderId:" + order_info.LinkedOrderId \
                # + " RefersToId:" + order_info.RefersToId \
                # + " TicketId:" + order_info.TicketId \
                # + " OriginalOrderId:" + order_info.OriginalOrderId \
                # + " PairSpreadType:" + order_info.PairSpreadType \
                print(f'The Stream response: {order_info.OrderId}, {order_info.Symbol}, Tag = {order_info.OrderTag}')
                tag_id = order_info.OrderTag
                now = time.perf_counter()

                with timing.lock:
                    submit_time = timing.submit_times.pop(tag_id, None)

                if submit_time is not None:
                    latency_ms = (now - submit_time) * 1000
                    print(
                        f"OrderTag {tag_id}: "
                        f"Submit => stream latency = {latency_ms:.2f} ms"
                    )
        except Exception as e:
            print(e)

    def send_single_order(self):
       
        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4())) #OrderTag
        single_order = ord.SubmitSingleOrderRequest()
        single_order.Symbol = self.symbol
        single_order.Side = self.side
        single_order.Quantity = self.quantity
        single_order.Route = self._route  # Route
        single_order.Staged = self._staged  # True if staged
        single_order.ClaimRequire = self._claim_required
        single_order.UserToken = self.xapiLib.userToken
        single_order.Account = self.order_account
        single_order.ReturnResult = self.get_order_details

        single_order.TimeInForce.Expiration = self._expiration
        if self._expiration == 6:  # in case a GTD(Good Till Date) order is placed, the ExpirationDate field must be given
            single_order.ExpirationDate.FromDatetime(datetime(year=2025, month=7, day=9))
        single_order.Price.value = self.prc
        single_order.StopPrice.value = self.prc + 3.500
        single_order.PriceType.PriceType = self.prc_type
        single_order.OrderTag = self.my_order_id

        single_order.ExtendedFields['ACCT_TYPE'] = '119'

        start = time.perf_counter()
        with timing.lock:
            timing.submit_times[self.my_order_id] = start
        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        print(f"The SubmitSingleOrder Response: {str(singleorder_submit_response.ServerResponse)} " +
              f"The RPC latency: {(time.perf_counter() - start)*1000:.2f} ms")
        # if single_order.ReturnResult:
        #     print("Order Details:" + str(singleorder_submit_response.OrderDetails))
        #     print("PriceType: " + str(
        #         singleorder_submit_response.OrderDetails.PriceType.PriceType))  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
    
if __name__ == '__main__':
    submit_order = CreateSingleOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_single_order()  # API call
    time.sleep(10)  
        
    submit_order.xapiLib.logout()