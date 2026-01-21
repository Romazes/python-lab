import enum
import time
from datetime import datetime, timedelta
from threading import Event, Thread
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary


class CreateSpreadOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.ready = Event()
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        self.my_order_id1 = 'XAP-{0}'.format(str(uuid4()))
        self.my_order_id2 = 'XAP-{0}'.format(str(uuid4()))
        self.underLyingSym = 'symbol'
        self.leg1symbol = 'optionsymbol-leg1'
        self._buy_sell1 = 'BUY/SELL'
        self.leg2symbol = 'optionsymbol-leg2'
        self._buy_sell2 = 'BUY/SELL'
        self._route = 'ROUTE'
        self.leg1_prc_type = ''  # Limit/Market
        self.leg1_prc = '123'
        self.leg2_prc_type = ''  # Limit/Market
        self.leg2_prc = '123'
        self.spreadquantity = 1  # Spead Quantity
        self.leg1ratio = 1  # Leg 1 Ratio
        self.leg2ratio = 2  # Leg 2 Ratio
        self.putOrCallLeg1 = 'C/P'  # C/P - CALL/PUT
        self.putOrCallLeg2 = 'C/P'  # C/P - CALL/PUT
        self.exchange = 'Exchange'
        self.parent_orderid = ''
        self.leg1_orderid = ''
        self.leg2_orderid = ''
        self.status = ''
        self.submitthenchangeorder = True  # When True sample modify script is executed when order goes LIVE.

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
                    # displaying only current spread order
                    if order_info.ExtendedFields['OrderTag'] == self.my_order_id or order_info.ExtendedFields[
                        'OrderTag'] == self.my_order_id1 or order_info.ExtendedFields['OrderTag'] == self.my_order_id2:
                        print('sym:{0} vol:{1} self.status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(
                            order_info.Symbol,
                            order_info.Volume, order_info.CurrentStatus, order_info.OrderId,
                            order_info.TicketId, order_info.Reason, order_info.ExtendedFields['OrderTag'],
                            order_info.Type))
                    self.currentOrder = False
                    if order_info.Type == 'UserSubmitCompoundOrder' and order_info.ExtendedFields[
                        'OrderTag'] == self.my_order_id:
                        # current order
                        self.currentOrder = True
                        self.parent_orderid = order_info.OrderId

                    elif order_info.Type == 'UserSubmitOrder' and order_info.ExtendedFields[
                        'OrderTag'] == self.my_order_id1:
                        self.currentOrder = True
                        self.leg1_orderid = order_info.OrderId

                    elif order_info.Type == 'UserSubmitOrder' and order_info.ExtendedFields[
                        'OrderTag'] == self.my_order_id2:
                        self.currentOrder = True
                        self.leg2_orderid = order_info.OrderId

                    # To check if Order is Live and send Change Order
                    if self.parent_orderid and self.leg1_orderid and self.leg2_orderid and self.status != State.ChangePending.name \
                            and self.currentOrder and self.submitthenchangeorder:
                        if order_info.Type == 'UserSubmitCompoundOrder' and order_info.CurrentStatus == 'LIVE':
                            print("ORDER LIVE -- SUBMITTING CHANGE")
                            self.change_order()

                    if order_info.Type == 'UserSubmitCompoundOrder':
                        if order_info.CurrentStatus == "COMPLETED" or order_info.CurrentStatus == "DELETED":
                            print("ORDER FINISHED")
                            self.status = State.OrderDone.name

            except Exception as e:
                print(e)

    def send_spread_order(self):
        # create order
        spread_Order = ord.BasketOrderRequest()
        account = self.order_account.split(';')
        ord_request = ord.OrderRow()
        ord_request.DispName = '!SPREAD'
        ord_request.Buyorsell = 'BUY'
        ord_request.PriceType = 'MARKET/LIMIT'
        ord_request.Undersym = self.underLyingSym
        ord_request.Price = '0.0'
        ord_request.VolumeType = 'AsEntered'
        ord_request.Volume.value = self.spreadquantity
        ord_request.Exchange = self.exchange
        ord_request.Styp.value = 21  # Security Type - 21 (Synthetic)
        ord_request.Bank = account[0]
        ord_request.Branch = account[1]
        ord_request.Customer = account[2]
        ord_request.Deposit = account[3]
        ord_request.GoodUntil = 'DAY'  # DAY,GTC,GTD..
        ord_request.Type = 'UserSubmitCompoundOrder'  # ORDER TYPE
        ord_request.Route = self._route
        ord_request.SpreadNumLegs.value = 2
        ord_request.LinkedOrderRelationship.value = 2  # 2 = Spread
        ord_request.LinkedOrderCancellation.value = 2  # Atomic = 1, AllOrNone = 2, AutonomousState = 3
        ord_request.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 1'
        ord_request.ExtendedFields['ORDER_TAG'] = self.my_order_id

        ord_Leg1 = ord.OrderRow()
        ord_Leg1.DispName = self.leg1symbol
        ord_Leg1.Buyorsell = self._buy_sell1
        ord_Leg1.PriceType = self.leg1_prc_type
        ord_Leg1.Undersym = self.underLyingSym
        ord_Leg1.ExpirDate.FromDatetime(datetime(year=2022, month=9, day=16))  # Expiration Date
        ord_Leg1.Price = self.leg1_prc
        ord_Leg1.VolumeType = 'AsEntered'
        ord_Leg1.Volume.value = self.spreadquantity * self.leg1ratio  # Calculates quantity based on leg ratio
        ord_Leg1.Exchange = self.exchange
        ord_Leg1.Styp.value = 2  # Security Type 2 - Stock Option
        ord_Leg1.Bank = account[0]
        ord_Leg1.Branch = account[1]
        ord_Leg1.Customer = account[2]
        ord_Leg1.Deposit = account[3]
        ord_Leg1.GoodUntil = 'DAY'  # DAY,GTC,GTD..
        ord_Leg1.Type = 'UserSubmitOrder'  # ORDER TYPE
        ord_Leg1.Route = self._route
        ord_Leg1.SpreadNumLegs.value = 2  # Number of Legs in spread strategy
        ord_Leg1.SpreadLegNumber.value = 1  # Leg number
        ord_Leg1.SpreadLegCount.value = 2  # Number of Legs in spread strategy
        ord_Leg1.Putcallind = self.putOrCallLeg1  # C- CALL Option, P - PUT Option
        ord_Leg1.LinkedOrderRelationship.value = 2  # 2 = Spread
        ord_Leg1.LinkedOrderId = self.my_order_id  # !SPREAD order ID
        ord_Leg1.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 2'
        ord_Leg1.ExtendedFields['ORDER_TAG'] = self.my_order_id1

        ord_Leg2 = ord.OrderRow()
        ord_Leg2.DispName = self.leg2symbol
        ord_Leg2.Buyorsell = self._buy_sell2
        ord_Leg2.PriceType = self.leg2_prc_type
        ord_Leg2.Undersym = self.underLyingSym
        ord_Leg2.ExpirDate.FromDatetime(datetime(year=2022, month=9, day=16)) # Expiration Date
        ord_Leg2.Price = self.leg2_prc
        ord_Leg2.VolumeType = 'AsEntered'
        ord_Leg2.Volume.value = self.spreadquantity * self.leg2ratio  # Calculates quantity based on leg ratio
        ord_Leg2.Exchange = self.exchange
        ord_Leg2.Styp.value = 2  # Security Type 2 - Stock Option
        ord_Leg2.Bank = account[0]
        ord_Leg2.Branch = account[1]
        ord_Leg2.Customer = account[2]
        ord_Leg2.Deposit = account[3]
        ord_Leg2.GoodUntil = 'DAY'  # DAY,GTC,GTD..
        ord_Leg2.Type = 'UserSubmitOrder'  # ORDER TYPE
        ord_Leg2.Route = self._route
        ord_Leg2.SpreadNumLegs.value = 2  # Number of Legs in spread strategy
        ord_Leg2.SpreadLegNumber.value = 2  # Leg number
        ord_Leg2.SpreadLegCount.value = 2  # Number of Legs in spread strategy
        ord_Leg2.Putcallind = self.putOrCallLeg2  # C- CALL Option, P - PUT Option
        ord_Leg2.LinkedOrderRelationship.value = 2  # 2 = Spread
        ord_Leg2.LinkedOrderId = self.my_order_id  # !SPREAD order ID
        ord_Leg2.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 3'
        ord_Leg2.ExtendedFields['ORDER_TAG'] = self.my_order_id2

        spread_Order.Orders.extend([ord_request, ord_Leg1, ord_Leg2])
        spread_Order.UserToken = self.xapiLib.userToken

        resp_spreadOrder = self.xapiLib.get_order_service_stub().SubmitBasketOrder(spread_Order)

        if resp_spreadOrder.ServerResponse == 'success':
            print("Successfully Submitted Spread Order")
        else:
            print(resp_spreadOrder.OptionalFields["ErrorMessage"])

    def change_order(self):
        print("Submitting Change for Spread Order ... ")
        user_input =input('Enter a key to submit change..:')
        # currently, supports spread orders with two legs.
        self.status = State.ChangePending.name
        self.spreadquantity = 10  # Example to update spread quantity
        chg_leg1qty = str(int(self.leg1ratio * self.spreadquantity))
        chg_leg2qty = str(int(self.leg2ratio * self.spreadquantity))
        change_spreadorder = ord.ChangePairOrderRequest(PairOrderId=self.parent_orderid,
                                                        Leg1OrderId=self.leg1_orderid,
                                                        Leg2OrderId=self.leg2_orderid,
                                                        Leg1_Quantity=int('0' + chg_leg1qty),
                                                        Leg2_Quantity=int('0' + chg_leg2qty),
                                                        UserToken=self.xapiLib.userToken
                                                        )
        # ExtendedFields['PRICE'] = '121'
        #Required to submit change for Spread order
        change_spreadorder.Leg1_ExtendedFields['LINKED_ORDER_RELATIONSHIP'] = '2'
        change_spreadorder.Leg2_ExtendedFields['LINKED_ORDER_RELATIONSHIP'] = '2'
        change_spreadorder.OptionalFields['LINKED_ORDER_RELATIONSHIP'] = '2'

        resp_change = self.xapiLib.get_order_service_stub().ChangePairOrder(change_spreadorder)
        if resp_change.ServerResponse == 'success':
            print("Successfully Changed Spread Order")
        else:  # FAILED TO CHANGE ORDER
            print(resp_change.OptionalFields["ErrorMessage"])


class State(enum.Enum):
    ConnectionPending = 0
    OrderPending = 1
    ChangePending = 2
    CancelPending = 3
    OrderFinished = 4
    ConnectionDead = 5
    ChangeCompleted = 6


if __name__ == "__main__":
    submit_order = CreateSpreadOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_spread_order()  # API call
    time.sleep(10)
    submit_order.xapiLib.logout()
