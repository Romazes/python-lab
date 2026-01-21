import xapi_client_support as imp

''''Function for Submit Basket Order'''
def submitbasketorder(self):
    try:
        basket_Order = imp.ob.BasketOrderRequest()
        ord_request = imp.ob.OrderRow()
        
        if self.aSelection == '':
            imp.tk.messagebox.showinfo("Message", 'Please select account')
            return False
        else:
            account = self.aSelection.split(";")
      
        ord_request.DispName = 'AAPL'
        ord_request.Buyorsell = 'BUY'
        ord_request.PriceType = 'AsEntered'
        ord_request.Price = '88.23'
        ord_request.VolumeType = 'AsEntered'
        ord_request.Volume.value = 989
        ord_request.Exchange = 'NYS'
        ord_request.Styp.value = 1
        ord_request.Bank = account[0]
        ord_request.Branch = account[1]
        ord_request.Customer = account[2]
        ord_request.Deposit = account[3]
        ord_request.GoodUntil = 'GTC'
        ord_request.Type = 'UserSubmitOrder'
        ord_request.Route = 'DEMOEUR'
        ord_request.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 1'

        ord_request1 = imp.ob.OrderRow()
        ord_request1.DispName = 'VOD.LSE'
        ord_request1.Buyorsell = 'SELL'
        ord_request1.PriceType = 'AsEntered'
        ord_request1.Price = '123'
        ord_request1.VolumeType = 'AsEntered'
        ord_request1.Volume.value = 688      
        ord_request1.Exchange = 'NYS'
        ord_request1.Styp.value = 1
        ord_request1.Bank = account[0]
        ord_request1.Branch = account[1]
        ord_request1.Customer = account[2]
        ord_request1.Deposit = account[3]
        ord_request1.GoodUntil = 'DAY'
        ord_request1.Type = 'UserSubmitOrder'
        ord_request1.Route = 'DEMOEUR'
        ord_request1.ExtendedFields['EZE_OMS_TRADER'] = 'OMS Trader Id 2'
        
        basket_Order.Orders.extend([ord_request, ord_request1])  
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
                
        basket_Order.UserToken = self.userToken
        self.resp_basketOrder = self.stub.SubmitBasketOrder(basket_Order)

        if self.resp_basketOrder.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Submitted Basket Order")
        else: 
            self.msg_basketOrder = self.resp_basketOrder.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_basketOrder)    
    
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
