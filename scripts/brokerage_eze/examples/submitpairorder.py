import xapi_client_support as imp

''''Funtion for Submit Pair Order'''
def submitpairorder(self):
    try:
        pairOrder = imp.ob.SubmitPairOrderRequest()
        
        pairOrder.Leg1_Symbol =  self.symbol.upper()         
        pairOrder.Leg1_Side   =  self.side.upper()          
        pairOrder.Leg1_Quantity = int('0'+ self.qty)  #to handle empty string added '0'         
        pairOrder.Leg2_Symbol = self.symbol_2.upper()         
        pairOrder.Leg2_Side =   self.side_2.upper() 
        pairOrder.Leg2_Quantity = int('0' + self.qty_2)  #to handle empty string added '0' 
        pairOrder.Route = self.route.upper() 
        if not self.aSelection:
            imp.tk.messagebox.showinfo("Message", "Please Select Account")
            return False

        pairOrder.Account = self.aSelection                
        pairOrder.Staged = self.staged_Order    
        pairOrder.ClaimRequire = self.claimRequired 

        #for routing child on the staged parent
        if self.order_ticketid:
            pairOrder.TicketId = self.order_ticketid 
        if self.order_ordertag:
            pairOrder.OrderTag = self.order_ordertag 
        #########

        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
        pairOrder.UserToken = self.userToken     

        '''Leg1 Extended fields'''
        if self.ext_Leg1:
            for extFields1, extValues1 in self.ext_Leg1.items():
                pairOrder.Leg1_ExtendedFields[extFields1] = extValues1 

        '''Leg2 Extended fields'''
        if self.ext_Leg2:
            for extFields2, extValues2 in self.ext_Leg2.items():
                pairOrder.Leg2_ExtendedFields[extFields2] = extValues2 

        '''Optional fields'''
        if self.Optional_field:
            for optFields, optValues in self.Optional_field.items():
                pairOrder.OptionalFields[optFields] = optValues   

        #handling SendPairOrder Server response
        self.resp_pairOrder = self.stub.SubmitPairOrder(pairOrder) 

        if self.resp_pairOrder.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Submitted Pair Order")
        else:
            self.msg_Order = self.resp_pairOrder.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_Order)  
                
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))