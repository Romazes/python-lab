import grpc
import time
from datetime import datetime, timedelta
from threading import Event, Thread
from uuid import uuid4
from srp import *
from srp import _pysrp
import hashlib
from emsxapilibrary import EMSXAPILibrary
import order_pb2
import order_pb2_grpc


class CreateAlgoOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

        self.symbol = 'MSFT'
        self.quantity = 123
        self.buy_sell = 'BUY/SELL/SELLSHORT/BUYTOCOVER'
        self.route = 'ROUTE/EXITVEHICLE'
        self.staged = False
        self.claim_req = False
        self.saved_strategy = 'ATDL_TYPE:SAVED_STRATEGYNAME'  # SAVED_STRATEGYNAME must be saved beforehand using RealTick UI, ATDL_TYPE can be looked up from BDX->Route Profile
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  # separated by semicolon CLient Trading account
        self.ready = Event()

    def start_listening(self):
        self.xapiLib.login()

        # start thread to listen to updates from the server about our orders
        self.thread = Thread(target=self.subscribe_order_info)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    # this is the thread func for the order listener
    def subscribe_order_info(self):
        subscribe_request = order_pb2.SubscribeOrderInfoRequest()
        subscribe_request.Level = 0
        subscribe_request.UserToken = self.xapiLib.userToken

        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        while True:
            try:
                if subscribe_response:
                    order_info = next(subscribe_response)

                    if order_info.ExtendedFields['ORDER_TAG'] == self.my_order_id:
                        print('sym:{0} vol:{1} status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(
                            order_info.Symbol,
                            order_info.Volume,
                            order_info.CurrentStatus,
                            order_info.OrderId,
                            order_info.TicketId,
                            order_info.ExtendedFields['Reason'],
                            order_info.ExtendedFields['ORDER_TAG'],
                            order_info.Type))

            except Exception as e:
                print(e)

    def send_algo_order(self):
        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        algo_order = order_pb2.SubmitSingleOrderRequest()
        algo_order.Symbol = self.symbol
        algo_order.Side = self.buy_sell
        algo_order.Quantity = self.quantity
        algo_order.Route = self.route  # EXITVEHICLE
        algo_order.ClaimRequire = self.claim_req
        algo_order.Staged = self.staged
        algo_order.UserToken = self.xapiLib.userToken
        algo_order.Account = self.order_account

        algo_order.ExtendedFields['ORDER_TAG'] = self.my_order_id
        algo_order.ExtendedFields['SAVED_STRATEGY_STRING_ID'] = self.saved_strategy
        algoorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(algo_order)
        print(algoorder_submit_response)


if __name__ == "__main__":
    submit_order = CreateAlgoOrder()
    submit_order.start_listening()
    submit_order.send_algo_order()
    time.sleep(30)  # time in seconds to wait before logging out; by default
    submit_order.xapiLib.logout()
    submit_order.xapiLib.close_channel()
