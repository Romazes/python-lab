import xapi_client_support as imp

'''Function for Add Symbols'''
def removesymbols(self):
    try:
        req_remsym = imp.md.RemoveSymbolsRequest()  
        req_remsym.UserToken = self.userToken 
        req_remsym.Symbols.extend(self.Sym_ip) 
        if self.marketLevel:
            req_remsym.MarketDataLevel = self.marketLevel 
        else:
            imp.tk.messagebox.showinfo("Message", "Please Select Market Level")  
            return False  
        self.resp_reqremsym = self.market_stub.RemoveSymbols(req_remsym)

        if self.resp_reqremsym.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Removed Symbols")
        else:
            self.resp_msg = self.resp_reqremsym.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)
            return False

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))