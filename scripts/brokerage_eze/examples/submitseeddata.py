import xapi_client_support as imp

''''Function for Seed Order'''
def submitseeddata(self):
        try:
            seed_Order = imp.ob.SubmitSeedDataRequest()       
            if not self.aSelection:
                imp.tk.messagebox.showinfo("Message", "Please Select Account")
                return False
                
            seed_Order.Account = self.aSelection     #Select the account from ACCOUNT combobox 
            seed_Order.Symbol = self.symbol.upper()
            if not self.userToken:
                imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
                return False
            
            seed_Order.UserToken = self.userToken
            self.resp_seedOrder = self.stub.SubmitSeedData(seed_Order)

            if self.resp_seedOrder.ServerResponse == self.success:
                imp.tk.messagebox.showinfo("Message","Successfully Sent Seed Security Message For Symbol")
            else: 
                self.msg_seedOrder = self.resp_seedOrder.OptionalFields["ErrorMessage"]
                imp.tk.messagebox.showinfo("Message", self.msg_seedOrder)    
        
        except Exception as e:
            imp.tk.messagebox.showinfo("Message", str(e))
