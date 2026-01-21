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
        self.symbol = 'symbol'
        self.quantity_prnt = 200
        self.side = 'BUY/SELL/SELLSHORT'  # parent_side
        self.route_prnt = 'ROUTE'  # parent_route
        self.staged_prnt = True
        self.claim_req_prnt = False
        self.parent_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  # separated by semicolon
        self.quantity_child = 100
        self.staged_child = False
        self.route_child = 'ROUTE'
        self.child_account = 'BANK,BRANCH,CUSTOMER,DEPOSIT'  # separated by comma
        self.ready = Event()
        self.order_live = False
        self.my_order_id = ''

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

                # if this is our parent order and it's live, signal to continue
                if order_info.Symbol == self.symbol and order_info.OrderTag == str(
                        self.my_order_id) and order_info.CurrentStatus == 'LIVE':
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
        parent_order.Side = self.side
        parent_order.Quantity = self.quantity_prnt
        parent_order.Staged = self.staged_prnt
        parent_order.Route = self.route_prnt
        # parent_order.ExtendedFields['EXIT_VEHICLE'] = 'NONE'
        parent_order.ClaimRequire = self.claim_req_prnt
        parent_order.UserToken = self.xapiLib.userToken
        parent_order.Account = self.parent_account
        parent_order.OrderTag = self.my_order_id
        parent_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(parent_order)
        print(parent_submit_response)

    def send_child_order(self):
        # route child on the staged parent
        child_order = ord.SubmitSingleOrderRequest()
        child_order.TicketId = self.my_order.OrderId
        child_order.Symbol = self.my_order.Symbol
        child_order.Side = self.my_order.Side
        child_order.Quantity = self.quantity_child
        child_order.Staged = self.staged_child
        child_order.UserToken = self.xapiLib.userToken
        child_order.Account = self.parent_account
        child_order.Route = 'NONE'
        child_order.ExtendedFields['DEST_ROUTE'] = 'DEMOEUR'
        child_order.ExtendedFields['ROUTING_BBCD'] = self.child_account
        child_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(child_order)
        print(child_submit_response)


if __name__ == "__main__":
    submit_order = CreateParentThenRouteChildOrderExample()
    submit_order.xapiLib.login()
    submit_order.start_listening()
    submit_order.send_parent_order()  # calling parent staged order
    submit_order.wait_for_parent_live()
    submit_order.send_child_order()  # calling child order from parent staged
    time.sleep(10)
    submit_order.xapiLib.logout()
