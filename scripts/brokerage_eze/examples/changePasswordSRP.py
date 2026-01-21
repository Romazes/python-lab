from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad
import xapi_client_support as imp
from srp import *
from srp import _pysrp
import hashlib


def changePasswordSRP(self):
    # srp login
    try:
        if len(self.credentials):
            u_name = self.credentials[0]
            domain_connect = self.credentials[1]
            identity = self.credentials[2]
            old_password = self.list_Start[2].get()
            new_password = self.list_Start[3].get()
            locale = self.credentials[3]
        else:
            u_name = self.list_Start[0].get()
            domain_connect = self.list_Start[1].get()
            identity = "@".join([u_name.upper(), domain_connect.upper()])
            old_password = self.list_Start[2].get()
            new_password = self.list_Start[3].get()
            locale = self.list_Start[4].get()

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
            hex_srp_n = hex(int('0' + srp_n))
            hex_s_n = ''
            if len(hex_srp_n) == 258:
                hex_s_n = hex_srp_n.lstrip('0x')

            int_g = int('0' + srp_g)
            bytes_g = int_g.to_bytes(128, 'big')

            if hex_s_n and srp_g:
                usr = _pysrp.User(identity, old_password, hash_alg=SHA256, ng_type=NG_CUSTOM, n_hex=hex_s_n, g_hex=srp_g)
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

            srp_M_int = int.from_bytes(M, 'big')
            srp_M_h = hex(srp_M_int)
            srp_M_hex = srp_M_h.lstrip('0x').upper()

            kc = usr.K
            SRPKey_int = int.from_bytes(kc, 'big')
            SRPKey = hex(SRPKey_int)
            srp_key = SRPKey.lstrip('0x').upper()

            srp_complogin = imp.uPb2.CompleteLoginSrpRequest()
            srp_complogin.Identity = identity
            srp_complogin.srpTransactId = srp_transactid
            srp_complogin.strEphA = str(srp_Ax)
            srp_complogin.strMc = srp_M_hex
            srp_complogin.UserName = u_name
            srp_complogin.Domain = domain_connect.upper()
            srp_complogin.Locale = locale
            self.resp_complogin = self.utility_stub.CompleteLoginSrp(srp_complogin)

            if self.resp_complogin.UserToken == 'null':
                imp.tk.messagebox.showinfo("Login Failed:User must successfully login to change the Password.")
                return

            # changepassword code

            iv = bytes(str(srp_Ax), 'ascii')
            IV = iv[0:16]

            ivrandom = [IV[x % 16] for x in range(16)]
            iv2 = bytes(ivrandom)

            kckey = [kc[x % 32] for x in range(32)]
            key = bytes(kckey)

            new_pswd = bytes(new_password, 'ascii')
            old_pswd = bytes(old_password, 'ascii')

            newPswd = pad(new_pswd, AES.block_size)
            oldPswd = pad(old_pswd, AES.block_size)

            # Encrypt passwords using GCM mode for authenticated encryption
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv2)
            newPwd, tag1 = cipher.encrypt_and_digest(newPswd)

            cipher2 = AES.new(key, AES.MODE_GCM, nonce=iv2)
            oldPwd, tag2 = cipher2.encrypt_and_digest(oldPswd)

            srp_newpwd_int = int.from_bytes(newPwd, 'big')
            srp_newpwd = hex(srp_newpwd_int)
            srp_newpwd_hex = srp_newpwd.lstrip('0x').upper()  # string

            srp_oldpwd_int = int.from_bytes(oldPwd, 'big')
            srp_oldpwd = hex(srp_oldpwd_int)
            srp_oldpwd_hex = srp_oldpwd.lstrip('0x').upper()  # string

            changepasswordsrp = imp.uPb2.ChangePasswordSRPRequest()
            changepasswordsrp.UserName = u_name
            changepasswordsrp.Domain = domain_connect
            changepasswordsrp.TransactId = srp_transactid
            changepasswordsrp.OldPassword = srp_oldpwd_hex
            changepasswordsrp.NewPassword = srp_newpwd_hex
            response = self.utility_stub.ChangePasswordSRP(changepasswordsrp)
            if response.status == "success":
                imp.tk.messagebox.showinfo("Message", "Password changed successfully. Please re-connect.")
                self.top_Start.destroy()
                self.top_Start = False
            else:
                imp.tk.messagebox.showinfo("Message", "Password change failed.")

    except Exception as e:
        imp.tk.messagebox.showinfo("Message", str(e))
