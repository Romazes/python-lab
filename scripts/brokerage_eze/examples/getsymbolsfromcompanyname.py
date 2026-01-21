import xapi_client_support as imp

def getsymbolsfromcompanyname(self):
    try:
        mkt = imp.md.SymbolsFromCompanyNameRequest() 
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False 
        mkt.CompanyName = self.list_Sym[0].get()   
        mkt.UserToken = self.userToken         
        self.resp_symData = self.market_stub.GetSymbolsFromCompanyName(mkt)
        
        if self.resp_symData.Acknowledgement.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Fetched Symbols From Company Name")
            return self.resp_symData
        else: 
            self.msg_symData = self.resp_symData.Acknowledgement.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_symData)   
            return False 

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))