import xapi_client_support as imp

''''Funtion for Cancel Pair Order'''
def cancelpairorder(self):
        try:
            pairCancel = imp.ob.CancelPairOrderRequest()
            if self.Orderlinkedid == '': 
                pairCancel.OrderId =  str(self.valcol)  
            else: #child order id is selected need to pass pair order id
                pairCancel.OrderId =  str(self.Orderlinkedid) 
            pairCancel.UserToken = self.userToken     

            self.resp_Cancel = self.stub.CancelPairOrder(pairCancel)
           
            if self.resp_Cancel.ServerResponse == self.success:
                imp.tk.messagebox.showinfo("Message","Successfully Cancel Order")
            else: #FAILED TO CANCEL ORDER
                self.msg_Cancel = self.resp_Cancel.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.msg_Cancel)                
        
        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))