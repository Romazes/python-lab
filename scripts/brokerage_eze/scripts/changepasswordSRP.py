from emsxapilibrary import EMSXAPILibrary
import utilities_pb2
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad

class ChangePasswordSRP:
    def __init__(self):  # set username, password, domain, locale, port number and server address details
        EMSXAPILibrary.create()
        self.xapiLib = EMSXAPILibrary.get()
        self.new_password = 'tal'  # enter the newpassword

    def encrption(self):
        # Encryting passwords

        iv = bytes(self.xapiLib.strEpha, 'ascii')
        IV = iv[0:16]

        ivrandom = [IV[x % 16] for x in range(16)]
        iv2 = bytes(ivrandom)

        kckey = [self.xapiLib.kc[x % 32] for x in range(32)]
        key = bytes(kckey)

        new_pswd = bytes(self.new_password, 'ascii')
        old_pswd = bytes(self.xapiLib.config.password, 'ascii')

        newPswd = pad(new_pswd, AES.block_size)
        oldPswd = pad(old_pswd, AES.block_size)

        cipher = AES.new(key, AES.MODE_GCM, nonce=iv2)  # method to encrypt newpassword
        newPwd, tag1 = cipher.encrypt_and_digest(newPswd)

        cipher2 = AES.new(key, AES.MODE_GCM, nonce=iv2)  # method to encrypt oldpassword
        oldPwd, tag2 = cipher2.encrypt_and_digest(oldPswd)

        srp_newpwd_int = int.from_bytes(newPwd, 'big')
        srp_newpwd = hex(srp_newpwd_int)
        srp_newpwd_hex = srp_newpwd.lstrip('0x').upper()  # string

        srp_oldpwd_int = int.from_bytes(oldPwd, 'big')
        srp_oldpwd = hex(srp_oldpwd_int)
        srp_oldpwd_hex = srp_oldpwd.lstrip('0x').upper()

        self.newPassword = srp_newpwd_hex
        self.oldPassword = srp_oldpwd_hex

    def change_password_srp(self):
        self.xapiLib.login()
        print('user token' + self.xapiLib.userToken)

        self.encrption()
        request = utilities_pb2.ChangePasswordSRPRequest()  # create changepassword request object
        request.TransactId = self.xapiLib.srp_transactid
        request.UserName = self.xapiLib.config.user
        request.Domain = self.xapiLib.config.domain
        request.OldPassword = self.oldPassword  # hexencoded oldPassword
        request.NewPassword = self.newPassword  # hexencoded newPassword
        response = self.xapiLib.get_utility_service_stub().ChangePasswordSRP(request)  # API call
        if response.status:
            print("Password Changed Successfully")
        else:
            print("Change password Failed")

if __name__ == "__main__":
    change_pswd_srp_example = ChangePasswordSRP()  # password
    change_pswd_srp_example.change_password_srp()
    change_pswd_srp_example.xapiLib.logout()
    change_pswd_srp_example.xapiLib.close_channel()