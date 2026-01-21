import xapi_client_support as imp

'''Function for UnSubscribeLevel1Data'''
def unsubscribelevel1data(self):
    try:
        req_L1Unsub = imp.md.UnSubscribeLevel1DataRequest() 
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False 
        req_L1Unsub.UserToken = self.userToken         
       
        self.resp_reqL1Unsub = self.market_stub.UnSubscribeLevel1Data(req_L1Unsub)

        if self.resp_reqL1Unsub.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Unsubscribed Level1 Data")
        else:
            self.resp_msg = self.resp_reqL1Unsub.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)
    
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))