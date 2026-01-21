import time
from threading import Event, Thread
import order_pb2 as ord
from emsxapilibrary import EMSXAPILibrary


class CreatePairOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.leg1symbol = 'leg1_symbol'
        self.leg1quantity = 1111
        self._buy_sell1 = 'BUY/SELL/BUYTOCOVER/SELLSHORT'
        self.leg2symbol = 'leg2_symbol'
        self.leg2quantity = 1000
        self._buy_sell2 = 'BUY/SELL/BUYTOCOVER/SELLSHORT'
        self._route = 'EXIT-VEHICLE/ROUTE'
        self._claim_required = False
        self._staged = False
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.order_ticketid = 'TICKET_ID'
        self.order_ordertag = 'ORDER_TAG'
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
        subscribe_request.Level = 0
        subscribe_request.UserToken = self.xapiLib.userToken
        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        while True:
            try:
                if subscribe_response:
                    order_info = next(subscribe_response)
                    print('sym:{0} vol:{1} status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(order_info.Symbol,
                                                                                                     order_info.Volume,
                                                                                                     order_info.CurrentStatus,
                                                                                                     order_info.OrderId,
                                                                                                     order_info.TicketId,
                                                                                                     order_info.Reason,
                                                                                                     order_info.ExtendedFields[
                                                                                                         'OrderTag'],
                                                                                                     order_info.Type))
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
        pairOrder.Leg2_Symbol = self.leg2symbol
        pairOrder.Leg2_Side = self._buy_sell2
        pairOrder.Leg2_Quantity = self.leg2quantity

        # for routing child on the staged parent
        # if self.order_ticketid:
        #     pairOrder.TicketId = self.order_ticketid 
        # if self.order_ordertag:
        #     pairOrder.OrderTag = self.order_ordertag 
        #########

        resp_pairOrder = self.xapiLib.get_order_service_stub().SubmitPairOrder(pairOrder)
        print(resp_pairOrder.ServerResponse)
        if resp_pairOrder.ServerResponse == 'Failed':
            print(resp_pairOrder.OptionalFields["ErrorMessage"])


if __name__ == "__main__":
    submit_order = CreatePairOrder()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_pair_order()  # API call
    time.sleep(10)   #time in seconds to wait before logging out
    submit_order.xapiLib.logout()