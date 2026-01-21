import time
from datetime import datetime, timedelta
from threading import Event, Thread, Lock
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary
import json

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
        self._expiration = 1  # DAY = 0, GTC = 1, GTX = 2, CLO = 3, OPG = 4, IOC = 5, GTD = 6, OTHER = 7
        self.prc = 120.740  # 'PRICE'
        self.prc_type = 1  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
        self._route = 'DEMOEUR'
        self.order_account = 'TAL;TEST;YGUO;1'
        self.ready = Event()

    def start_listening(self):
        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self.subscribe_order_info)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    # this is the thread func for the order listener
    def subscribe_order_info(self):
        subscribe_request = ord.SubscribeOrderInfoJsonRequest()
        subscribe_request.UserToken = self.xapiLib.userToken
        subscribe_request.Filters.IncludeOrders = True
        subscribe_request.Filters.IncludeExecutions = True

        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfoJson(subscribe_request) # 2
        self.ready.set()

        try:
            try:
                for detail_json in subscribe_response:
                    order_info_list = json.loads(detail_json.OrderInfoJson)
                    for order_info in order_info_list:
                        tag_id = order_info.get("OrderTag")

                        now = time.perf_counter()

                        with timing.lock:
                            submit_time = timing.submit_times.pop(tag_id, None)

                        if submit_time is not None:
                            latency_ms = (now - submit_time) * 1000
                            print(
                                f"OrderTag {tag_id}: "
                                f"Submit => stream latency = {latency_ms:.2f} ms"
                            )
                            # print(detail_json.OrderInfoJson)
                        
            except Exception as e:
                print(f'Inner: Exception: {e}')
        except Exception as e:
            print(f'Outer: Exception: {e}')

    def send_single_order(self):
        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        single_order = ord.SubmitSingleOrderRequest()
        single_order.Symbol = self.symbol
        single_order.Side = self.side
        single_order.Quantity = self.quantity
        single_order.Route = self._route  # Route
        single_order.Staged = self._staged  # True if staged
        single_order.ClaimRequire = self._claim_required
        single_order.UserToken = self.xapiLib.userToken
        single_order.Account = self.order_account

        if self._expiration == 6:  # in case a GTD(Good Till Date) order is placed, the ExpirationDate field must be given
            single_order.ExpirationDate.FromDatetime(datetime(year=2025, month=7, day=17))
        single_order.TimeInForce.Expiration = self._expiration  # add other enum values in the comments.
        single_order.Price.value = self.prc
        single_order.StopPrice.value = self.prc + 3.500
        single_order.PriceType.PriceType = 0
        single_order.OrderTag = self.my_order_id

        ######OMS FILEDS if required
        # single_order.ExtendedFields['EZE_OMS_MANAGER'] = ''
        # single_order.ExtendedFields['EZE_OMS_TRADER']  = ''
        # single_order.ExtendedFields['USER_STRATEGY']   = ''
        # single_order.ExtendedFields['REASON_CODE']     = ''
        # single_order.ExtendedFields['CUSTODIAN']       = ''
        ##################
        start = time.perf_counter()
        with timing.lock:
            timing.submit_times[self.my_order_id] = start
        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        print(f'The SubmitSingleOrder (OrderTag: {self.my_order_id}): {singleorder_submit_response}. The RPC latency: {(time.perf_counter() - start)*1000:.2f} ms')

if __name__ == '__main__':
    submit_order = CreateSingleOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_single_order()  # API call
    time.sleep(10) #time in seconds to wait before logging out
    submit_order.xapiLib.logout()