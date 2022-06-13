import datetime
import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

def get_date_time():
    return str(datetime.datetime.now())

def write_local_error_log (e):
    # get the date to make it a bit easier
    file = open("error_logs.txt", "a")
    file.write(str(e))
    file.write("\n")
    file.close()
    
def upload_err_log(err_text, t):
    body = {'auth_sec_2':config["AUTH_SEC_2"], 'error_text':err_text}
    headers = {'auth_p1': config["AUTH_P1"], 'auth_sec_2': config["AUTH_SEC_2"],'authorization': "lkasjdoicm " + t}
    target_url = 'https://'+config["IP"]+':'+config["PORT"]+'/'+config["PICTURE_ROUTE"]+'/'+config["ERROR_ROUTE"]
    # make the post request
    requests.post(target_url, headers=headers, data=body, verify=config["CERT"])

def get_file(file_path):
    return file_path.split('/')[-1]

# master function to handle the entire pipeline
def handle_error_log(py_file, err_text):
    try:
        # get the token
        f = open('.cached')
        t = f.read()
        f.close()
        # first log the error locally
        error_text = '##' + get_date_time() + "## " + get_file(py_file) + " - " + err_text
        write_local_error_log(error_text)
        # then try and see if we can upload it.
        upload_err_log(error_text, t)
    except Exception as err:
        write_local_error_log("ERR LOG FAILURE: " + str(err))


