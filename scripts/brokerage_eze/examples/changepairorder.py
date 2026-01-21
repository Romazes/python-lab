import xapi_client_support as imp

''''Function for Change Pair Order'''
def changepairorder(self):
    try:
        pairChange = imp.ob.ChangePairOrderRequest() 
        if self.Orderlinkedid == '':
            pairChange.PairOrderId = str(self.valcol)
        else:
           pairChange.PairOrderId = self.childIds['Pair OrderId']        
        pairChange.Leg1OrderId = self.childIds['Leg1 OrderId']        
        pairChange.Leg2OrderId = self.childIds['Leg2 OrderId']         
        qty_Leg1change = self.list_changePair[0].get()
        qty_Leg2change = self.list_changePair[1].get()
        pairChange.Leg1_Quantity = int('0' + qty_Leg1change)   
        pairChange.Leg2_Quantity = int('0' + qty_Leg2change)   
        pairChange.UserToken = self.userToken

        '''Leg1 Extended fields'''
        if self.extchange_Leg1:
            for extFields1_pairs, extValues1_pairs in self.extchange_Leg1.items():
                pairChange.Leg1_ExtendedFields[extFields1_pairs] = extValues1_pairs 

        '''Leg2 Extended fields'''
        if self.extchange_Leg2:
            for extFields2_pairs, extValues2_pairs in self.extchange_Leg2.items():
                pairChange.Leg2_ExtendedFields[extFields2_pairs] = extValues2_pairs 

        '''Optional fields'''
        if self.extchange_Opt:
            for optFields_pairs, optValues_pairs in self.extchange_Opt.items():
                pairChange.OptionalFields[optFields_pairs] = optValues_pairs 

        self.resp_Change = self.stub.ChangePairOrder(pairChange)

        if self.resp_Change.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Changed Pair Order")
        else: #FAILED TO CHANGE ORDER
            self.msg_Change = self.resp_Change.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_Change)    
        
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))





