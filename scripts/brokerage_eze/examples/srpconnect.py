import xapi_client_support as imp
from srp import *
from srp import _pysrp
import hashlib

'''Function to fetch the GLX2 token from server'''
def srpconnect(self):
    try:
        self.credentials.clear()
        u_name = self.list_Start[0].get()
        domain_connect = self.list_Start[1].get()
        identity = "@".join([u_name.upper(), domain_connect.upper()])
        pswrd_connect = self.list_Start[2].get()
        locale_connect = self.list_Start[3].get()
        self.credentials.append(u_name)
        self.credentials.append(domain_connect)
        self.credentials.append(identity)
        self.credentials.append(locale_connect)
        srp_login = imp.uPb2.StartLoginSrpRequest()
        srp_login.UserName = u_name
        srp_login.Domain = domain_connect
        resp_Startloginsrp = self.utility_stub.StartLoginSrp(srp_login)
        if resp_Startloginsrp.Response == self.success:
            srp_transactid = resp_Startloginsrp.srpTransactId
            srp_g = resp_Startloginsrp.srpg
            srp_n = resp_Startloginsrp.srpN
            srp_b = resp_Startloginsrp.srpb
            srp_salt = resp_Startloginsrp.srpSalt

            srp_salt_byte = bytes.fromhex(srp_salt)

            int_b = int('0' + srp_b)
            srp_b_bytes = int_b.to_bytes(128, 'big')

            int_n = int('0' + srp_n)
            bytes_n = int_n.to_bytes(128, 'big')
            hex_s_n = bytes_n.hex()

            int_g = int('0' + srp_g)
            bytes_g = int_g.to_bytes(128, 'big')
            hex_g = bytes_g.hex()

            if hex_s_n and srp_g:
                usr = _pysrp.User( identity, pswrd_connect, hash_alg=SHA256, ng_type=NG_CUSTOM, n_hex=hex_s_n, g_hex=hex_g)
                concate_ng = bytes_n + bytes_g
                k_ng = hashlib.sha256(concate_ng).hexdigest()
                k_bytes = bytes.fromhex(k_ng)
                usr.k = int.from_bytes(k_bytes, 'big')
                uname, A = usr.start_authentication()

            if A is None:
                imp.tk.messagebox.showinfo("Message", "Failed")

            srp_Ax = int.from_bytes(A, 'big')

            # Server => Client: s, B 
            M = usr.process_challenge(srp_salt_byte, srp_b_bytes)

            if M is None:
                imp.tk.messagebox.showinfo("Message", "Failed")

            srp_M_hex = M.hex()

            srp_complogin = imp.uPb2.CompleteLoginSrpRequest()
            srp_complogin.Identity = identity
            srp_complogin.srpTransactId = srp_transactid
            srp_complogin.strEphA = str(srp_Ax)
            srp_complogin.strMc = srp_M_hex
            srp_complogin.UserName = u_name
            srp_complogin.Domain = domain_connect.upper()
            srp_complogin.Locale = locale_connect.upper()
            self.resp_complogin = self.utility_stub.CompleteLoginSrp(srp_complogin)

            if self.resp_complogin.Response:
                if self.resp_complogin.Response == self.success:
                    self.userToken = self.resp_complogin.UserToken
                    self.credentials.append(self.userToken)
                    imp.tk.messagebox.showinfo("Message", "Successfully Fetched UserToken")
                    self.top_Start.destroy()
                    self.top_Start = False
                else:
                    imp.tk.messagebox.showinfo("Message", self.resp_complogin.Response)
                    return False
            else:
                imp.tk.messagebox.showinfo("Message", "Failed To Fetch  UserToken")
                return False
        else:
            imp.tk.messagebox.showinfo("Message", "Failed To Fetch  UserToken")
            return False
        return True
    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
