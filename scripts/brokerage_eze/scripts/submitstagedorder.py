import time
from datetime import datetime
from threading import Event, Thread
from uuid import uuid4
import order_pb2 as ord
from emsxapilibrary import EMSXAPILibrary


class CreateSingleStagedOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'symbol'
        self.quantity = 123  # Quantity/volume
        self.side = 'BUY/SELL/SELLSHORT'
        self._staged = True
        self._claim_required = False
        self._expiration = 6  # DAY = 0, GTC = 1, GTX = 2, CLO = 3, OPG = 4, IOC = 5, GTD = 6, OTHER = 7
        self.prc = 132.500
        self.prc_type = 1  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
        self._route = 'ROUTE'
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
        except Exception as e:
            print(e)

    def send_single_stagedorder(self):
        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        single_stgorder = ord.SubmitSingleOrderRequest()
        single_stgorder.Symbol = self.symbol
        single_stgorder.Side = self.side
        single_stgorder.Quantity = self.quantity
        single_stgorder.Route = self._route  # Route
        single_stgorder.Staged = self._staged  # True if staged
        single_stgorder.ClaimRequire = self._claim_required
        single_stgorder.UserToken = self.xapiLib.userToken
        single_stgorder.Account = self.order_account

        single_stgorder.TimeInForce.Expiration = self._expiration
        if self._expiration == 6:  # in case a GTD(Good Till Date) order is placed, the ExpirationDate field must be given
            single_stgorder.ExpirationDate.FromDatetime(datetime(year=2021, month=7, day=9))
        single_stgorder.Price.value = self.prc
        single_stgorder.StopPrice.value = self.prc + 3.500
        single_stgorder.PriceType.PriceType = self.prc_type
        single_stgorder.OrderTag = self.my_order_id

        ######OMS FILEDS if required
        # single_stgorder.ExtendedFields['EZE_OMS_MANAGER'] = ''
        # single_stgorder.ExtendedFields['EZE_OMS_TRADER']  = ''
        # single_stgorder.ExtendedFields['USER_STRATEGY']   = ''
        # single_stgorder.ExtendedFields['REASON_CODE']     = ''
        # single_stgorder.ExtendedFields['CUSTODIAN']       = ''
        ##################
        stagedorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_stgorder)
        print(stagedorder_submit_response)

if __name__ == '__main__':
    submit_order = CreateSingleStagedOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_single_stagedorder()  # API call
    time.sleep(10)  #time in seconds to wait before logging out; by default, its 3min but it can be modified based on the workflow and requirements
    submit_order.xapiLib.logout()