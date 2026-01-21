import xapi_client_support as imp

''''Funtion for Submit Trade Report'''
def submittradereport(self):
    try:
        '''Mandatory fields to place an order'''
        trd_report = imp.ob.SubmitTradeReportRequest()
        trd_report.Symbol = self.symbol.upper()
        trd_report.Side =   self.side.upper()      
        trd_report.Quantity = int('0' + self.qty)  #to handle empty string added '0' 
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False 
        
        trd_report.UserToken = self.userToken 
        trd_report.Route = self.route.upper()   

        trade_type = imp.ob.TradeType()   
        if self.trade_ordtype:
            if self.trade_ordtype == 'UserSubmitTradeReport':
                trade_type.OrderTypes = 0  
            elif self.trade_ordtype == 'ForeignExecution':
                trade_type.OrderTypes = 1
            else:
                imp.tk.messagebox.showinfo("Message", "Please Select Event Type")
        trd_report.OrderType.OrderTypes = trade_type.OrderTypes 

        if self.aSelection == '':
            imp.tk.messagebox.showinfo("Message", "Please Select Account")
            return False
        else:
            trd_report.Account = self.aSelection        

        '''Extended fields'''
        if self.ext_Leg: #price/exp
            for extFields, extValues in self.ext_Leg.items():
                trd_report.ExtendedFields[extFields] = extValues 
             
        #handling SendOrder Server response
        self.resp_Order = self.stub.SubmitTradeReport(trd_report) 
        if self.resp_Order.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message","Successfully Submitted Trade Report")
        else:
            self.msg_Order = self.resp_Order.OptionalFields["ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.msg_Order)
                 
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))

