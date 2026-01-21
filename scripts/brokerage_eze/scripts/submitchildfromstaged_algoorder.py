import time
from threading import Event, Thread
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary


class CreateParentThenRouteChildOrderExample:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.ready = Event()
        self.symbol = 'symbol'
        self.quantity_prnt = 200
        self.buy_sell = 'BUY/SELL/SELLSHORT/BUYTOCOVER'  # parent_side
        self.route_prnt = 'ROUTE/EXITVEHICLE'  # parent_route
        self.staged_prnt = True
        self.claim_req_prnt = False
        self.parent_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  # separated by semicolon
        self.quantity_child = 100
        self.staged_child = False
        self.route_child = 'ROUTE/EXITVEHICLE'
        self.saved_strategy = 'USERNAME:USER_FIRMNAME:ATDL_TYPE:SAVED_STRATNAME'
        self.child_account = 'BANK,BRANCH,CUSTOMER,DEPOSIT'  # separated by comma
        self.ready = Event()
        self.order_live = False

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
                                                                                                     order_info.ExtendedFields[
                                                                                                         'Reason'],
                                                                                                     order_info.ExtendedFields[
                                                                                                         'ORDER_TAG'],
                                                                                                     order_info.Type))

                    # if this is our parent order and it's live, signal to continue
                    if order_info.Symbol == self.symbol and order_info.Volume == str(
                            self.quantity_prnt) and order_info.CurrentStatus == 'LIVE':
                        print('Parent order is live.')
                        self.my_order = order_info
                        self.order_live = True
            except Exception as e:
                print(e)

    def wait_for_parent_live(self):
        while not self.order_live:
            time.sleep(1)

    def send_parent_order(self):
        # create staged order
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        parent_order = ord.SubmitSingleOrderRequest()
        parent_order.Symbol = self.symbol
        parent_order.Side = self.buy_sell
        parent_order.Quantity = self.quantity_prnt
        parent_order.Staged = self.staged_prnt
        parent_order.Route = self.route_prnt
        # parent_order.ExtendedFields['EXIT_VEHICLE'] = 'NONE'
        parent_order.ClaimRequire = self.claim_req_prnt
        parent_order.UserToken = self.xapiLib.userToken
        parent_order.Account = self.parent_account
        parent_order.ExtendedFields['ORDER_TAG'] = self.my_order_id
        parent_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(parent_order)
        print(parent_submit_response)

    def send_child_order(self):
        # route child on the staged parent
        child_order = ord.SubmitSingleOrderRequest()
        child_order.ExtendedFields['TICKET_ID'] = self.my_order.OrderId
        child_order.Symbol = self.my_order.Symbol
        child_order.Side = self.my_order.Buyorsell
        child_order.Quantity = self.quantity_child
        child_order.Staged = self.staged_child
        child_order.UserToken = self.xapiLib.userToken
        child_order.Account = self.parent_account
        child_order.Route = self.route_child  # ROUTE
        # child_order.ExtendedFields['EXIT_VEHICLE'] = 'STAGE'
        # child_order.ExtendedFields['DEST_ROUTE'] = 'DEMOEUR'
        child_order.ExtendedFields['ROUTING_BBCD'] = self.child_account
        # Algo name to be named after the ATDLType
        child_order.ExtendedFields['SAVED_STRATEGY_STRING_ID'] = self.saved_strategy
        child_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(child_order)
        print(child_submit_response)


if __name__ == "__main__":
    submit_order = CreateParentThenRouteChildOrderExample()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_parent_order()  # calling parent staged order
    submit_order.wait_for_parent_live()
    submit_order.send_child_order()  # calling child order from parent staged

    time.sleep(10)  # time in seconds to wait before logging out
    submit_order.xapiLib.logout()
