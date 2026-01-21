import time
from threading import Event, Thread
from uuid import uuid4
import order_pb2 as ord
import order_pb2_grpc as ord_grpc
from emsxapilibrary import EMSXAPILibrary

class CreateBasketOrder:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.order_account = 'BANK;BRANCH;CUSTOMER;DEPOSIT'
        self.ready = Event()
        self.stop = Event()

    def stop_listening(self):
        self.stop.set()

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
            if(self.stop.is_set()):
                print('Time to stop')
                break

            try:
                if subscribe_response:
                    order_info = next(subscribe_response)
                    # displaying only current basket order
                    if order_info.ExtendedFields['OrderTag'] == self.my_order_id or order_info.ExtendedFields[
                        'OrderTag'] == self.my_order_id1:
                        print('sym:{0} vol:{1} self.status:{2} oid:{3} tid:{4} r:{5} ot:{6} otype:{7}'.format(
                            order_info.Symbol,
                            order_info.Volume, order_info.CurrentStatus, order_info.OrderId,
                            order_info.TicketId, order_info.Reason, order_info.ExtendedFields['OrderTag'],
                            order_info.Type))
            except Exception as e:
                print(e)

    def send_basket_order(self):
        # create order
        basket_Order = ord.BasketOrderRequest()
        account = self.order_account.split(';')

        ord_request = ord.OrderRow()
        self.my_order_id = 'XAP-{0}'.format(str(uuid4()))
        ord_request.DispName = 'SYMBOL'
        ord_request.Buyorsell = 'BUY/SELL/BUYTOCOVER/SELLSHORT'
        ord_request.PriceType = 'AsEntered/LIMIT'
        ord_request.Price = 'PRICE_VALUE'
        ord_request.VolumeType = 'AsEntered/LIMIT'
        ord_request.Volume.value = 123  # volume
        ord_request.Exchange = 'EXCHANGE'
        ord_request.Styp.value = 1
        ord_request.Bank = account[0]
        ord_request.Branch = account[1]
        ord_request.Customer = account[2]
        ord_request.Deposit = account[3]
        ord_request.GoodUntil = 'EXPIRATION'  # DAY,GTC,GTD..
        ord_request.Type = 'UserSubmitOrder'  # ORDERTYPE
        ord_request.Route = 'ROUTE'
        ord_request.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 1'
        ord_request.ExtendedFields['ORDER_TAG'] = self.my_order_id

        ord_request1 = ord.OrderRow()
        self.my_order_id1 = 'XAP-{0}'.format(str(uuid4()))
        ord_request1.DispName = 'SYMBOL'
        ord_request1.Buyorsell = 'BUY/SELL/BUYTOCOVER/SELLSHORT'
        ord_request1.PriceType = 'AsEntered/LIMIT'
        ord_request1.Price = 'PRICE_VALUE'
        ord_request1.VolumeType = 'AsEntered/LIMIT'
        ord_request1.Volume.value = 123  # volume
        ord_request1.Exchange = 'EXCHANGE'
        ord_request1.Styp.value = 1
        ord_request1.Bank = account[0]
        ord_request1.Branch = account[1]
        ord_request1.Customer = account[2]
        ord_request1.Deposit = account[3]
        ord_request1.GoodUntil = 'EXPIRATION'  # DAY,GTC,GTD..
        ord_request1.Type = 'UserSubmitOrder'  # ORDERTYPE
        ord_request1.Route = 'ROUTE'
        ord_request1.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 2'
        ord_request1.ExtendedFields['ORDER_TAG'] = self.my_order_id1

        basket_Order.Orders.extend([ord_request, ord_request1])

        basket_Order.UserToken = self.xapiLib.userToken
        resp_basketOrder = self.xapiLib.get_order_service_stub().SubmitBasketOrder(basket_Order)

        if resp_basketOrder.ServerResponse == 'success':
            print("Successfully Submitted Basket Order")
        else:
            print(resp_basketOrder.OptionalFields["ErrorMessage"])

            # Method for logging out

if __name__ == "__main__":
    submit_order = CreateBasketOrder()
    try:
        submit_order.xapiLib.login()
        submit_order.start_listening()
        submit_order.send_basket_order()

        time.sleep(10)

        submit_order.stop_listening()
        submit_order.xapiLib.logout()
        submit_order.xapiLib.close_channel()
    except Exception as e:
        print(e)
