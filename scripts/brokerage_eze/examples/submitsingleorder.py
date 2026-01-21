import xapi_client_support as imp

''''Funtion for Submit Single Order'''
def submitsingleorder(self):
    try:
        '''Mandatory fields to place an order'''
        Order = imp.ob.SubmitSingleOrderRequest()
        Order.Symbol = self.symbol.upper()
        Order.Side =   self.side.upper()      
        Order.Quantity = int('0' + self.qty)  #to handle empty string added '0'                                          
        Order.Route = self.route.upper()                               
        Order.Staged = self.staged_Order                                 
        Order.ClaimRequire = self.claimRequired 

        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
        Order.UserToken = self.userToken
        if not self.aSelection:
            imp.tk.messagebox.showinfo("Message", "Please Select Account")
            return False
        Order.Account = self.aSelection  

        #for routing child on the staged parent 
        if self.order_ticketid:
            Order.TicketId = self.order_ticketid 
        if self.order_ordertag:
            Order.OrderTag = self.order_ordertag 
        #######

        '''Extended fields'''
        if self.ext_Leg:
            for extFields, extValues in self.ext_Leg.items():
                Order.ExtendedFields[extFields] = extValues 
             
        #handling SendOrder Server response
        self.resp_Order = self.stub.SubmitSingleOrder(Order) 
        if self.resp_Order.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Submitted Single Order")
        else:
            self.msg_Order = self.resp_Order.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_Order)
                 
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))

