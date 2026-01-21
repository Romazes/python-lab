import xapi_client_support as imp

'''Function for Add Symbols'''
def addsymbols(self):
    try:
        req_addsym = imp.md.AddSymbolsRequest()  
        req_addsym.UserToken = self.userToken 
        req_addsym.Symbols.extend(self.Sym_ip)
        if not self.marketLevel:
            imp.tk.messagebox.showinfo("Message", "Please Select Market Level")  
            return False   
        req_addsym.MarketDataLevel = self.marketLevel 
        self.resp_reqaddsym = self.market_stub.AddSymbols(req_addsym)

        if self.resp_reqaddsym.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Added Symbols")
        else:
            self.resp_msg = self.resp_reqaddsym.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)
            return False

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))