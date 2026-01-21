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
        # Create field selection with custom field combination
        # field_selection = ord.SubscribeOrderFieldOptions()

        # Select specific standard fields based on proto definition
        # field_selection.RequestedFields.extend([
        #     ord.SubscribeOrderFieldOptions.Fields.SUBMIT_TIME,
        #     ord.SubscribeOrderFieldOptions.Fields.ORDER_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.LINKED_ORDER_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.REFERS_TO_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.TICKET_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.ORIGINAL_ORDER_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.SYMBOL,
        #     ord.SubscribeOrderFieldOptions.Fields.TYPE,
        #     ord.SubscribeOrderFieldOptions.Fields.CURRENT_STATUS,
        #     ord.SubscribeOrderFieldOptions.Fields.TRADER_ID,
        #     ord.SubscribeOrderFieldOptions.Fields.CLAIMED_BY_CLERK,
        #     ord.SubscribeOrderFieldOptions.Fields.VOLUME,
        #     ord.SubscribeOrderFieldOptions.Fields.PRICE,
        #     ord.SubscribeOrderFieldOptions.Fields.PRICE_TYPE,
        #     ord.SubscribeOrderFieldOptions.Fields.BUYORSELL,
        #     ord.SubscribeOrderFieldOptions.Fields.PAIR_SPREAD_TYPE,
        #     ord.SubscribeOrderFieldOptions.Fields.REASON,
        #     ord.SubscribeOrderFieldOptions.Fields.TIME_STAMP,
        #     ord.SubscribeOrderFieldOptions.Fields.EXTENDED_FIELDS,
        #     ord.SubscribeOrderFieldOptions.Fields.GOOD_FROM,
        #     ord.SubscribeOrderFieldOptions.Fields.TIME_IN_FORCE,
        #     ord.SubscribeOrderFieldOptions.Fields.STOP_PRICE,
        #     ord.SubscribeOrderFieldOptions.Fields.USER_MESSAGE,
        #     ord.SubscribeOrderFieldOptions.Fields.EXPIRATION_DATE,
        #     ord.SubscribeOrderFieldOptions.Fields.SIDE,
        #     ord.SubscribeOrderFieldOptions.Fields.ROUTE,
        #     ord.SubscribeOrderFieldOptions.Fields.ACCOUNT,
        #     ord.SubscribeOrderFieldOptions.Fields.ORDER_TAG,
        #     ord.SubscribeOrderFieldOptions.Fields.VOLUME_TRADED
        # ])

        # Request specific extended fields (FIDs)
        # field_selection.RequestedExtendedFields.extend([
        #     "OriginalTraderId",  # Example FID 100
        #     "VolumeTraded",  # Example FID 101
        #     "ClOrdID",  # Client Order ID
        #     "OrigClOrdID"  # Original Client Order ID
        # ])

        # subscribe_request.FieldSelection.CopyFrom(field_selection)
        print(subscribe_request.UserToken)
        subscribe_response = self.xapiLib.get_order_service_stub().SubscribeOrderInfo(subscribe_request)
        self.ready.set()

        try:
            for order_info in subscribe_response:
                # Print both wire size (serialized) and in-memory size (RAM footprint)
                # try:
                #     # Wire size (serialized size)
                #     wire_size = len(order_info.SerializeToString())
                #     print(f"Wire size (serialized): {wire_size} bytes")

                #     # In-memory size (RAM footprint) using sys.getsizeof
                #     import sys
                #     memory_size = sys.getsizeof(order_info)
                #     print(f"In-memory size (RAM footprint): {memory_size} bytes")

                #     # Additional detailed memory calculation (recursive for nested objects)
                #     def get_deep_size(obj, seen=None):
                #         size = sys.getsizeof(obj)
                #         if seen is None:
                #             seen = set()

                #         obj_id = id(obj)
                #         if obj_id in seen:
                #             return 0

                #         # Important mark as seen *before* entering recursion
                #         seen.add(obj_id)

                #         if isinstance(obj, dict):
                #             size += sum([get_deep_size(v, seen) for v in obj.values()])
                #             size += sum([get_deep_size(k, seen) for k in obj.keys()])
                #         elif hasattr(obj, '__dict__'):
                #             size += get_deep_size(obj.__dict__, seen)
                #         elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
                #             size += sum([get_deep_size(i, seen) for i in obj])

                #         return size

                #     deep_memory_size = get_deep_size(order_info)
                #     print(f"Deep memory size (including nested objects): {deep_memory_size} bytes")

                # except Exception as size_err:
                #     print(f"Could not determine response sizes: {size_err}")
                # print("Extended Fields:")
                # for key, value in order_info.ExtendedFields.items():
                #     print(f"  {key}: {value}")
                print(order_info)
                break
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
        singleorder_submit_response = self.xapiLib.get_order_service_stub().SubmitSingleOrder(single_order)
        print("Server Response:" + str(singleorder_submit_response.ServerResponse))
        if single_order.ReturnResult:
            print("Order Details:" + str(singleorder_submit_response.OrderDetails))
            print("PriceType: " + str(
                singleorder_submit_response.OrderDetails.PriceType.PriceType))  # Market = 0, Limit = 1, StopMarket = 2, StopLimit = 3, Other = 4


if __name__ == '__main__':
    submit_order = CreateSingleOrder()
    submit_order.xapiLib.login()
    # print(submit_order.xapiLib.userToken)
    if not submit_order.get_order_details:
        submit_order.start_listening()
    submit_order.send_single_order()  # API call
    time.sleep(10)
    submit_order.xapiLib.logout()
