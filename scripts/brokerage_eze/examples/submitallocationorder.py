import xapi_client_support as imp

'''Function to DISCONNECT from server'''
def submitallocationorder(self):
    try:
        allocreq = imp.ob.SubmitAllocationOrderRequest()
        allocreq.UserToken = self.userToken  
        allocreq.OrderId = str(self.valcol)   
        allocreq.Symbol = self.symcol  
        allocreq.Exchange = self.exchange 
        source_acc = ';'.join([ self.bank_, self.branch_, self.customer_, self.deposit_ ])
        allocreq.SourceAccount = source_acc
        allocreq.TargetAccount = self.tgAcctselection   
        if self.source_qty:
            allocreq.TargetQuantity = int(float(self.source_qty))
        if self.source_prc:
            allocreq.TargetPrice = int(float(self.source_prc)) 

        typeoforder = imp.ob.OrderType()   
        if self.Ordertypecol:
            if self.Ordertypecol == 'UserSubmitOrder':
                typeoforder.TypeOfOrder = 0  
            elif self.Ordertypecol == 'ForeignExecution':
                typeoforder.TypeOfOrder = 1
            else:
                imp.tk.messagebox.showinfo("Message", "Can only build allocation from UserSubmitOrder or ForeignExectuion")
                return False
        allocreq.OrderTypes.TypeOfOrder = typeoforder.TypeOfOrder   
        

        typeofalloc = imp.ob.AllocationType()      
        if self.type_alloc:
            if self.type_alloc == 'UserSubmitAllocation':
                typeofalloc.AllocationOrAllocationEx = 0  
            else:   #UserSubmitAllocationEx
                typeofalloc.AllocationOrAllocationEx = 1

        allocreq.TypeOfAllocation.AllocationOrAllocationEx = typeofalloc.AllocationOrAllocationEx

        self.resp_alloc = self.stub.SubmitAllocationOrder(allocreq)
        if self.resp_alloc.ServerResponse == self.success:
            imp.tk.messagebox.showinfo("Message", "Successfully Allocated")
        else:
            self.resp_msg = self.resp_alloc.OptionalFields[
                "ErrorMessage"]
            imp.tk.messagebox.showinfo("Message", self.resp_msg)
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
