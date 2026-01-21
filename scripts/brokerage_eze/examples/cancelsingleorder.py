import xapi_client_support as imp

''''Funtion for Cancel Order'''
def cancelsingleorder(self):
        try:
            Order = imp.ob.CancelSingleOrderRequest()
            Order.OrderId =  str(self.valcol)  
            Order.UserToken = self.userToken     

            self.resp_Cancel = self.stub.CancelSingleOrder(Order)
           
            if self.resp_Cancel.ServerResponse == self.success:
                imp.tk.messagebox.showinfo("Message","Successfully Cancel Order")
            else: #FAILED TO CANCEL ORDER
                self.msg_Cancel = self.resp_Cancel.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.msg_Cancel)                
        
        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))