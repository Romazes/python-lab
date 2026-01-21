import time
from datetime import datetime
from threading import Event, Thread
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary


class CreateSingleOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.symbol = 'AAPL'
        self.quantity = 1233  # Quantity/volume
        self.side = 'BUY/SELL/SELLSHORT'
        self._staged = False
        self._claim_required = False
        self._expiration = 3  # DAY = 0, GTC = 1, GTX = 2, CLO = 3, OPG = 4, IOC = 5, GTD = 6, OTHER = 7
        self.prc = 120.520
        self.prc_type = 1  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4
        self._route = 'ROUTE'
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.get_order_details = False  # True/False, Returns Order Details when set to True
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
        subscribe_request.UserToken = self.xapiLib.userToken
        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        try:
            for order_info in subscribe_response:
                scalar_map = order_info.ExtendedFields
                print(scalar_map)
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
                          + " " + "FIX_MSG:" + scalar_map.get('FIX_MSG') \
                          + " " +"FIX_MSG_15508:" + scalar_map.get('FIX_MSG_15508') \
                          + " " + "FIX_MSG_15509:" + scalar_map.get('FIX_MSG_15509') \
                + " " + "FIX_MSG_15510:" + scalar_map.get('FIX_MSG_15510') \
               # + " " + "GENERIC_COMMENT:" + scalar_map.get('GENERIC_COMMENT') \

                    # + " LinkedOrderId:" + order_info.LinkedOrderId \
                # + " RefersToId:" + order_info.RefersToId \
                # + " TicketId:" + order_info.TicketId \
                # + " OriginalOrderId:" + order_info.OriginalOrderId \
                # + " PairSpreadType:" + order_info.PairSpreadType \
                print(message)

        except Exception as e:
            print(e)


    def send_single_order(self):

        # create order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))  # OrderTag
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
            single_order.ExpirationDate.FromDatetime(datetime(year=2021, month=7, day=9))
        single_order.Price.value = self.prc
        single_order.StopPrice.value = self.prc + 3.500
        single_order.PriceType.PriceType = self.prc_type
        single_order.OrderTag = self.my_order_id

        ######OMS FILEDS if required
        # single_order.ExtendedFields['EZE_OMS_MANAGER'] = ''
        # single_order.ExtendedFields['EZE_OMS_TRADER']  = ''
        # single_order.ExtendedFields['USER_STRATEGY']   = ''
        # single_order.ExtendedFields['REASON_CODE']     = ''
        # single_order.ExtendedFields['CUSTODIAN']       = ''
        ##################
        single_order.ExtendedFields['FIX_MSG'] = 'TEST-FIX_MSG'
        single_order.ExtendedFields['FIX_MSG_15508'] = 'TEST-FIX_MSG_15508'
        single_order.ExtendedFields['FIX_MSG_15509'] = 'TEST-FIX_MSG_15509'
        single_order.ExtendedFields['FIX_MSG_15510'] = 'TEST-FIX_MSG_15510'
        single_order.ExtendedFields['GENERIC_COMMENT'] = 'TEST-GENERIC_COMMENT'

        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        print("Server Response:" + str(singleorder_submit_response.ServerResponse))
        if single_order.ReturnResult:
            print("Order Details:" + str(singleorder_submit_response.OrderDetails))
            print("PriceType: " + str(
                singleorder_submit_response.OrderDetails.PriceType.PriceType))  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4


if __name__ == '__main__':
    submit_order = CreateSingleOrder()
    submit_order.xapiLib.login()
    if not submit_order.get_order_details:
        submit_order.start_listening()
    submit_order.send_single_order()  # API call
    time.sleep(10)

    submit_order.xapiLib.logout()