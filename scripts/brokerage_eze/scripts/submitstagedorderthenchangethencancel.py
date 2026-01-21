from datetime import datetime
import time
from threading import Event, Thread
from uuid import uuid4
import enum
import order_pb2 as ord
from emsxapilibrary import EMSXAPILibrary
from submitorderthenchangethencancel import State


class CreateSingleStagedOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'symbol'
        self.quantity = 3000
        self.side = 'BUY/SELL/SELLSHORT'
        self.route = 'ROUTE'
        self.staged = True
        self.claim_req = False
        self._expiration = 6  # DAY = 0, GTC = 1, GTX = 2, CLO = 3, OPG = 4, IOC = 5, GTD = 6, OTHER = 7
        self.prc = 432.500
        self.prc_type = 1  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.ready = Event()
        self.status = State.ConnectionPending.name  # status used for change and cancel order
        self.my_chgorder_tag = ''

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
                if order_info.OrderTag == self.my_order_id or order_info.OrderTag == self.my_chgorder_tag:
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

                    if self.status == State.ChangePending.name and order_info.Type == 'UserSubmitChange':
                        if order_info.CurrentStatus == 'COMPLETED':
                            print("CHANGE COMPLETED -- SUBMITTING CANCEL")
                            self.status = State.CancelPending.name
                            cancel_order = ord.CancelSingleOrderRequest(OrderId=self.ord_order_id,
                                                                        UserToken=self.xapiLib.userToken)
                            resp_Cancel = self.xapiLib.get_order_service_stub().CancelSingleOrder(cancel_order)
                            if resp_Cancel.ServerResponse == 'success':
                                print("Successfully Cancel Order")
                            else:  # FAILED TO CANCEL ORDER
                                print(resp_Cancel.OptionalFields["ErrorMessage"])
                        elif order_info.CurrentStatus == 'DELETED':
                            print("CHANGE FAILED -- SUBMITTING CANCEL ANYWAY")
                            self.status = State.CancelPending.name
                            cancel_order = ord.CancelSingleOrderRequest(OrderId=self.ord_order_id,
                                                                        UserToken=self.xapiLib.userToken)
                            resp_Cancel = self.xapiLib.get_order_service_stub().CancelSingleOrder(cancel_order)
                            if resp_Cancel.ServerResponse == 'success':
                                print("Successfully Cancel Order")
                            else:  # FAILED TO CANCEL ORDER
                                print(resp_Cancel.OptionalFields["ErrorMessage"])

                    elif self.status == State.OrderPending.name and order_info.Type == 'UserSubmitStagedOrder':
                        if order_info.CurrentStatus == 'LIVE':
                            print("ORDER LIVE -- SUBMITTING CHANGE")

                            self.ord_order_id = order_info.OrderId
                            self.status = State.ChangePending.name
                            self.my_chgorder_tag = 'XAP-{0}'.format(str(uuid4()))
                            qty = 3500  # order_info.Volume/ 2
                            change_order = ord.ChangeSingleOrderRequest(OrderId=order_info.OrderId,
                                                                        UserToken=self.xapiLib.userToken,
                                                                        Quantity=qty
                                                                        )  # Price.value = 121
                            change_order.OrderTag = self.my_chgorder_tag
                            resp_Change = self.xapiLib.get_order_service_stub().ChangeSingleOrder(change_order)
                            if resp_Change.ServerResponse == 'success':
                                print("Successfully Changed Order")
                            else:  # FAILED TO CHANGE ORDER
                                print(resp_Change.OptionalFields["ErrorMessage"])

                        elif order_info.CurrentStatus == "COMPLETED" or order_info.CurrentStatus == "DELETED":
                            print("ORDER UNEXPECTEDLY FINISHED")
                            self.status = State.OrderFinished.name

                    elif self.status == State.CancelPending.name:
                        if order_info.CurrentStatus == "COMPLETED" and order_info.CurrentStatus == "DELETED":
                            self.status = State.OrderFinished.name

                    if order_info.Symbol == self.symbol and order_info.Volume == self.quantity and order_info.Type == 'ExchangeTradeOrder':
                        print('GOT FILL FOR {0} {1} AT {2}'.format(order_info.Side, order_info.Volume,
                                                                   order_info.Price.value))

                    if order_info.Symbol == self.symbol and order_info.Volume == self.quantity and order_info.Type == 'ExchangeKillOrder':
                        print('GOT KILL')

        except Exception as e:
            print(e)

    def send_single_stgorder(self):
        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        single_order = ord.SubmitSingleOrderRequest()
        single_order.Symbol = self.symbol
        single_order.Side = self.side
        single_order.Quantity = self.quantity
        single_order.Route = self.route  # Route
        single_order.ClaimRequire = self.claim_req
        single_order.Staged = self.staged
        single_order.UserToken = self.xapiLib.userToken
        single_order.Account = self.order_account
        single_order.TimeInForce.Expiration = self._expiration
        if self._expiration == 6:  # in case a GTD(Good Till Date) order is placed, the ExpirationDate field must be given
            single_order.ExpirationDate.FromDatetime(datetime(year=2021, month=7, day=9))
        single_order.Price.value = self.prc
        single_order.StopPrice.value = self.prc + 3.500
        single_order.PriceType.PriceType = self.prc_type
        single_order.OrderTag = self.my_order_id
        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        self.status = State.OrderPending.name
        print(singleorder_submit_response)

class State(enum.Enum):
    ConnectionPending = 0
    OrderPending = 1
    ChangePending = 2
    CancelPending = 3
    OrderFinished = 4
    ConnectionDead = 5


if __name__ == "__main__":
    submit_order = CreateSingleStagedOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_single_stgorder()  # API call
    time.sleep(10)  #time in seconds to wait before logging out; by default, its 3min but it can be modified based on the workflow and requirements
    submit_order.xapiLib.logout()