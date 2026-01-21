import time
from threading import Event, Thread
from uuid import uuid4
import enum
import order_pb2 as ord
from emsxapilibrary import EMSXAPILibrary


class CreatePairOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.leg1symbol = 'leg1_symbol'
        self.leg1quantity = 100  # leg1_qty
        self._buy_sell1 = 'BUY/SELL_LEG1'
        self.leg2symbol = 'leg2_symbol'
        self.leg2quantity = 2000  # leg2_qty
        self._buy_sell2 = 'BUY/SELL_LEG2'
        self._route = 'ROUTE/EXITVEHICLE'
        self._staged = False
        self._claim_required = False
        self.leg1_prc = 'PRICE_LEG1'
        self.leg1_prc_type = 'PRICETYPE_LEG1'  # Limit/Market
        self.leg2_prc = 'PRICE_LEG2'
        self.leg2_prc_type = 'PRICETYPE_LEG2'  # Limit/Market
        self.ready = Event()
        self.status = State.WaitingForConnect.name  # status used for change and cancel order
        self.leg1order_tag = 'XAP-{0}'.format(str(uuid4()))
        self.leg2order_tag = 'XAP-{0}'.format(str(uuid4()))
        self.pair_orderid = ''
        self.leg1_orderid = ''
        self.leg2_orderid = ''

    def start_listening(self):
        # start thread to listen to updates from the server about our orders        
        self.thread = Thread(target=self.subscribe_order_info)
        self.thread.start()

        # wait for the subscription thread to signal ready
        self.ready.wait()

    # this is the thread func for the order listener
    def subscribe_order_info(self):
        subscribe_request = ord.SubscribeOrderInfoRequest()
        subscribe_request.Level = 0
        subscribe_request.UserToken = self.xapiLib.userToken
        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        while True:
            try:
                if subscribe_response:
                    order_info = next(subscribe_response)

                    if order_info.ExtendedFields['OrderTag'] == self.leg1order_tag \
                            or order_info.ExtendedFields[
                        'OrderTag'] == self.leg2order_tag:  # make sure update is for our orders (in case someone else is trading is same account)

                        print('sym:{0} vol:{1} status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(
                            order_info.Symbol,
                            order_info.Volume, order_info.CurrentStatus, order_info.OrderId,
                            order_info.TicketId, order_info.Reason, order_info.ExtendedFields['OrderTag'],
                            order_info.Type))

                        if order_info.Type == 'UserSubmitCompoundOrder':
                            self.pair_orderid = order_info.OrderId
                        elif order_info.Type == 'UserSubmitOrder' and order_info.ExtendedFields[
                            'OrderTag'] == self.leg1order_tag:
                            self.leg1_orderid = order_info.OrderId
                        elif order_info.Type == 'UserSubmitOrder' and order_info.ExtendedFields[
                            'OrderTag'] == self.leg2order_tag:
                            self.leg2_orderid = order_info.OrderId

                        if self.pair_orderid and self.leg1_orderid and self.leg2_orderid and self.status != State.ChangePending.name \
                                and self.status != State.CancelPending.name:

                            if order_info.Type == 'UserSubmitCompoundOrder' and order_info.CurrentStatus == 'LIVE':
                                print("ORDER LIVE -- SUBMITTING CHANGE")
                                self.status = State.ChangePending.name
                                # here, changing vol using USCO since, all leg1 order data is assigned to Pair
                                chg_leg1qty = str(int(order_info.Volume * 2))
                                chg_leg2qty = str(int(self.leg2quantity * 2))
                                change_prorder = ord.ChangePairOrderRequest(PairOrderId=self.pair_orderid,
                                                                            Leg1OrderId=self.leg1_orderid,
                                                                            Leg2OrderId=self.leg2_orderid,
                                                                            Leg1_Quantity=int('0' + chg_leg1qty),
                                                                            Leg2_Quantity=int('0' + chg_leg2qty),
                                                                            UserToken=self.xapiLib.userToken
                                                                            )  # ExtendedFields['PRICE'] = '121'
                                # change_prorder.Leg1_ExtendedFields['PAIR_RATIO'] = '2'
                                # change_prorder.Leg2_ExtendedFields[''] = ''
                                # change_prorder.OptionalFields[''] = ''
                                resp_Change = self.xapiLib.get_order_service_stub().ChangePairOrder(change_prorder)
                                if resp_Change.ServerResponse == 'success':
                                    print("Successfully Changed Pair Order")
                                else:  # FAILED TO CHANGE ORDER
                                    print(resp_Change.OptionalFields["ErrorMessage"])
                            if self.status == State.ChangePending.name and order_info.Type == 'UserSubmitCompoundOrder' and order_info.CurrentStatus == 'COMPLETED':
                                # now send cancel
                                print("Submitting Cancel for Pair Order ... ")
                                cancel_prorder = ord.CancelPairOrderRequest(OrderId=self.pair_orderid,  # pair order id
                                                                            UserToken=self.xapiLib.userToken)
                                self.status = State.CancelPending.name
                                resp_Cancel = self.xapiLib.get_order_service_stub().CancelPairOrder(cancel_prorder)
                                if resp_Cancel.ServerResponse == 'success':
                                    print("Successfully Cancelled Pair Order")
                                else:  # FAILED TO CANCEL ORDER
                                    print(resp_Cancel.OptionalFields["ErrorMessage"])

                            if order_info.Type == 'UserSubmitCompoundOrder':
                                if order_info.CurrentStatus == "COMPLETED" or order_info.CurrentStatus == "DELETED":
                                    print("ORDER UNEXPECTEDLY FINISHED")
                                    self.status = State.OrderDone.name
            except Exception as e:
                print(e)

    def send_pair_order(self):
        # create order
        pairOrder = ord.SubmitPairOrderRequest()
        pairOrder.Route = self._route
        pairOrder.Account = self.order_account
        pairOrder.Staged = self._staged
        pairOrder.ClaimRequire = self._claim_required
        pairOrder.UserToken = self.xapiLib.userToken

        pairOrder.Leg1_Symbol = self.leg1symbol
        pairOrder.Leg1_Side = self._buy_sell1
        pairOrder.Leg1_Quantity = self.leg1quantity
        pairOrder.Leg1_ExtendedFields['PRICE'] = self.leg1_prc
        pairOrder.Leg1_ExtendedFields['PRICE_TYPE'] = self.leg1_prc_type
        pairOrder.Leg1_ExtendedFields['ORDER_TAG'] = self.leg1order_tag

        pairOrder.Leg2_Symbol = self.leg2symbol
        pairOrder.Leg2_Side = self._buy_sell2
        pairOrder.Leg2_Quantity = self.leg2quantity
        pairOrder.Leg2_ExtendedFields['PRICE'] = self.leg2_prc
        pairOrder.Leg2_ExtendedFields['PRICE_TYPE'] = self.leg2_prc_type
        pairOrder.Leg2_ExtendedFields['ORDER_TAG'] = self.leg2order_tag

        resp_pairOrder = self.xapiLib.get_order_service_stub().SubmitPairOrder(pairOrder)
        print(resp_pairOrder.ServerResponse)
        if resp_pairOrder.ServerResponse == 'Failed':
            print(resp_pairOrder.OptionalFields["ErrorMessage"])


class State(enum.Enum):
    WaitingForConnect = 0
    OrderInPlay = 1
    OrderDone = 2
    ChangePending = 3
    CancelPending = 4
    ConnectionFailed = 5


if __name__ == "__main__":
    submit_order = CreatePairOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_pair_order()  # API call
    time.sleep(10)   #time in seconds to wait before logging out
    submit_order.xapiLib.logout()
