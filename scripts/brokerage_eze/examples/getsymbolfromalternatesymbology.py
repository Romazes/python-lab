import xapi_client_support as imp

def getsymbolfromalternatesymbology(self):
    try:
        mkt = imp.md.SymbolFromAlternateSymbologyRequest()  
        mkt.Symbol = self.list_Sym[0].get()  
        ord_request = imp.md.AlternateSymbology()         
        ord_request.SymbolOption = int(self.symlookup) #ISIN = 0;SEDOL = 1;RIC = 2;CUSIP = 3;BBG = 4
        mkt.SymbolInfo.SymbolOption = ord_request.SymbolOption 
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False          
        mkt.UserToken = self.userToken 
        self.resp_symInfo = self.market_stub.GetSymbolFromAlternateSymbology(mkt)
        
        if self.resp_symInfo.Acknowledgement.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Fetched Symbol From SEDOL, ISIN, CUSIP, etc")
            return self.resp_symInfo
        else: 
            self.msg_symInfo = self.resp_symInfo.Acknowledgement.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_symInfo)
            return False

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))