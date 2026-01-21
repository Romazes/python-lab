import xapi_client_support as imp

'''Instantiate the Stream response'''
def init_respStream(self):
    thread = imp.threading.Thread(target=subscribeorderinfo, args=[self])
    thread.name = 'OrderBlotterThread'
    thread.daemon = True
    thread.start()
        
''' Function for streaming response from gRPC server '''
def subscribeorderinfo(self):
    try:
        sblevel = imp.ob.SubscribeOrderInfoRequest()
        sblevel.Level = 0
        if not self.userToken:
            imp.tk.messagebox.showinfo("Message", 'No UserToken. Please Reconnect...')
            return False
            
        sblevel.UserToken = self.userToken
        self.resp = self.stub.SubscribeOrderInfo(sblevel)

        while True:
            if self.resp:
                sym = next(self.resp)
                # if sym.CurrentStatus == 'LIVE': ''' if you want to filter ''''
                self.ord_blotter.insert('', 'end', values=(format(sym.OrderId), format(sym.ExtendedFields['OrderTag']), format(sym.Symbol), format(sym.Buyorsell), 
                format(sym.Volume),format(sym.Price.value), format(sym.PriceType.PriceTypesEnum.Name(sym.PriceType.PriceType)), format(sym.CurrentStatus), format(sym.ExtendedFields['ExitVehicle']),
                format(sym.ExtendedFields['Bank']), format(sym.ExtendedFields['Branch']), format(sym.ExtendedFields['Customer']), format(sym.ExtendedFields['Deposit']),
                format(sym.Type), format(sym.LinkedOrderId), format(sym.RefersToId),format(sym.OriginalOrderId),
                format(sym.TraderId), format(sym.ExtendedFields['VolumeTraded']), format(sym.ExtendedFields['Exchange']),
                format(sym.ExtendedFields['Currency']),format(sym.Reason), format(sym.ExtendedFields['GoodFrom']), 
                format(sym.ExtendedFields['GoodUntil']), format(sym.ExtendedFields['SpreadNumLegs']),
                format(sym.ExtendedFields['PairSpreadType']), format(sym.ExtendedFields['PairTarget']), 
                format(sym.ExtendedFields['PairSpread']), format(sym.ExtendedFields['PairRatio']),
                format(sym.ExtendedFields['PairCash']), format(sym.ExtendedFields['NewsDate']), format(sym.ExtendedFields['OmsClientType']), 
                format(sym.ExtendedFields['GwBookSeqNo']),format(sym.ExtendedFields['UserMessage']), format(sym.ClaimedByClerk), format(sym.TimeStamp)))
                self.orderList.append(sym)

    except StopIteration as er:
        imp.tk.messagebox.showinfo("Message", er)