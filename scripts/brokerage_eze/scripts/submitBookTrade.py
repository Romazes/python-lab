from uuid import uuid4
import order_pb2 as ord
from emsxapilibrary import EMSXAPILibrary


class CreateBooktrade:
    def __init__(self):
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()

    def send_book_trade(self):
        # Book Trade details
        self.my_order_id = 'USSO_Order_ID'  ## USSO OrderID
        self.SourceAccount = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  ## SourceAccount
        self.OrderTag = 'XAP-{0}'.format(str(uuid4()))  # OrderTag

        ## 1st Allocation
        alloc_request1 = ord.AllocationDetails()
        alloc_request1.TargetAccount = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  ## Target Account
        alloc_request1.TargetQuantity = 1000  ## Target Quantity
        alloc_request1.TargetPrice.value = 1000  ## Target Price
        alloc_request1.AllocationDestinationRoute = 'Destination Route'
        alloc_request1.CommissionRate.value = 0  ##CommissionRate
        alloc_request1.CommissionRateType.value = 0  ##CommissionRateType ##CommissionRate #0-Per Share #1-Basis Point #-1-Flat rate #2-Discount rate
        alloc_request1.NetPrice.value = 1000  ##NetPrice
        alloc_request1.GeneralMessage = 'GeneralMessage'  ##GeneralMessage

        ## 2nd Allocation
        alloc_request2 = ord.AllocationDetails()
        alloc_request2.TargetAccount = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  ## Target Account
        alloc_request2.TargetQuantity = 1000  ## Target Quantity
        alloc_request2.TargetPrice.value = 1000  ## Target Price
        alloc_request2.AllocationDestinationRoute = 'Destination Route'
        alloc_request2.CommissionRate.value = 0  ##CommissionRate
        alloc_request2.CommissionRateType.value = 0  ##CommissionRateType ##CommissionRate #0-Per Share #1-Basis Point #-1-Flat rate #2-Discount rate
        alloc_request2.NetPrice.value = 1000  ##NetPrice
        alloc_request2.GeneralMessage = 'GeneralMessage'  ##GeneralMessage

        ## 3rd Allocation
        alloc_request3 = ord.AllocationDetails()
        alloc_request3.TargetAccount = 'BANK;BRANCH;CUSTOMER;DEPOSIT'  ## Target Account
        alloc_request3.TargetQuantity = 1000  ## Target Quantity
        alloc_request3.TargetPrice.value = 1000  ## Target Price
        alloc_request3.AllocationDestinationRoute = 'Destination Route'
        alloc_request3.CommissionRate.value = 0  ##CommissionRate
        alloc_request3.CommissionRateType.value = 0  ##CommissionRateType #0-Per Share #1-Basis Point #-1-Flat rate #2-Discount rate
        alloc_request3.NetPrice.value = 1000  ##NetPrice
        alloc_request3.GeneralMessage = 'GeneralMessage'  ##GeneralMessage

        ## Create Trade
        book_trade = ord.SubmitBookTradeRequest()

        book_trade.AllocDetails.extend([alloc_request1, alloc_request2,
                                        alloc_request3])  ## number of allocations can be changed as per requirement

        book_trade.UserToken = self.xapiLib.userToken  ## User Token
        book_trade.OrderTag = self.OrderTag  ## Set the order tag
        book_trade.OrderId = self.my_order_id  ## Set the orderId
        book_trade.SourceAccount = self.SourceAccount  ## Source Account from USO

        ## Submit the book trade request
        book_trade_submit_response = self.xapiLib.get_order_service_stub().SubmitBookTrade(book_trade)
        print(book_trade_submit_response)

    ##=========================================================================================================================
    ## Ignore everything downwards from this point.
    ## if you are not interested in the order output

    ##=========================================================================================================================
    ## Ignore everything downwards from this point.
    ## Technical hashing and login stuff in case you are interested
    ##=========================================================================================================================


if __name__ == '__main__':
    book_trade = CreateBooktrade()
    book_trade.xapiLib.login()

    book_trade.send_book_trade()

    book_trade.xapiLib.logout()
