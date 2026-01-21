import grpc
import time
from datetime import datetime, timedelta
from threading import Event, Thread
from uuid import uuid4
from srp import *
from srp import _pysrp
import hashlib
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
import utilities_pb2 as util
import utilities_pb2_grpc as util_grpc
from emsxapilibrary import EMSXAPILibrary


class CreateSingleOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'symbol'
        self.quantity = 3333
        self.side = 'BUY/SELL/SELLSHORT'
        self.route = 'ROUTE'
        self.staged = False
        self.claim_req = False
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
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
        subscribe_request.UserToken = self.xapiLib.userToken

        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        try:
            for order_info in subscribe_response:
                if order_info.OrderTag == self.my_order_tag:
                    # printing only currently placed order
                    message = "OrderId: " + order_info.OrderId \
                              + " Symbol:" + order_info.Symbol \
                              + " Type:" + order_info.Type \
                              + " CurrentStatus:" + order_info.CurrentStatus \
                              + " Volume:" + str(order_info.Volume) \
                              + " VolumeTraded:" + str(order_info.VolumeTraded) \
                              + " Price:" + str(order_info.Price.value) \
                              + " PriceType:" + order_info.PriceType.PriceTypesEnum.Name(order_info.PriceType.PriceType) \
                              + " Reason:" + order_info.Reason \
                              + " TimeStamp:" + str(order_info.TimeStamp) \
                              + " GoodFrom:" + str(order_info.GoodFrom) \
                              + " TimeInForce:" + order_info.TimeInForce.ExpirationTypes.Name(
                        order_info.TimeInForce.Expiration) \
                              + " StopPrice:" + str(order_info.StopPrice) \
                              + " UserMessage:" + order_info.UserMessage \
                              + " ExpirationDate:" + order_info.ExpirationDate.ToJsonString() \
                              + " Side:" + order_info.Side \
                              + " Route:" + order_info.Route \
                              + " Account:" + order_info.Account \
                              + " OrderTag:" + order_info.OrderTag \
                              + " TraderId:" + order_info.TraderId \
                              + " ClaimedByClerk:" + order_info.ClaimedByClerk \
                        # + " LinkedOrderId:" + order_info.LinkedOrderId \
                    # + " RefersToId:" + order_info.RefersToId \
                    # + " TicketId:" + order_info.TicketId \
                    # + " OriginalOrderId:" + order_info.OriginalOrderId \
                    # + " PairSpreadType:" + order_info.PairSpreadType \
                    print(message)

                    if order_info.Symbol == self.symbol and order_info.Type == 'UserSubmitOrder':
                        if order_info.CurrentStatus == 'COMPLETED' or order_info.CurrentStatus == 'DELETED':
                            print('Order is Completed or Deleted.')

                    if order_info.Symbol == self.symbol and order_info.Type == 'ExchangeTradeOrder':
                        print('GOT FILL FOR {0} {1} AT PRICE {2}'.format(order_info.Side, order_info.Volume,
                                                                         order_info.Price.value))

                    if order_info.Symbol == self.symbol and order_info.Type == 'ExchangeKillOrder':
                        print('GOT KILL')

        except Exception as e:
            print(e)

    def send_single_order(self):
        # create order
        self.my_order_tag = 'XAP-{0}'.format(str(uuid4()))
        single_order = ord.SubmitSingleOrderRequest()
        single_order.Symbol = self.symbol
        single_order.Side = self.side
        single_order.Quantity = self.quantity
        single_order.Route = self.route  # ROUTE
        single_order.ClaimRequire = self.claim_req
        single_order.Staged = self.staged
        single_order.UserToken = self.xapiLib.userToken
        single_order.Account = self.order_account
        single_order.OrderTag = self.my_order_tag
        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        print(singleorder_submit_response)


if __name__ == "__main__":
    submit_order = CreateSingleOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_single_order()  # API call
    time.sleep(10)  # time in seconds to wait before logging out;

    submit_order.xapiLib.logout()
    submit_order.xapiLib.close_channel()