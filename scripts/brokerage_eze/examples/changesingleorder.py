import xapi_client_support as imp

''''Function for Change Order'''
def changesingleorder(self):
        try:
            changeOrder = imp.ob.ChangeSingleOrderRequest()       
            qty_Order = self.list_changeSingle[0].get()   
            changeOrder.OrderId = str(self.valcol) 
            changeOrder.Quantity = int('0' + qty_Order)     #to handle empty string added '0'
            changeOrder.UserToken = self.userToken

            '''Extended fields'''
            if self.extchange_Leg1:
                for extFields_Change, extValues_Change in self.extchange_Leg1.items():
                    changeOrder.ExtendedFields[extFields_Change] = extValues_Change  

            self.resp_Change = self.stub.ChangeSingleOrder(changeOrder)

            if self.resp_Change.ServerResponse == self.success:
                imp.tk.messagebox.showinfo("Message","Successfully Changed Order")
            else: #FAILED TO CHANGE ORDER
                self.msg_Change = self.resp_Change.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.msg_Change)   
            return True 
        
        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))





    