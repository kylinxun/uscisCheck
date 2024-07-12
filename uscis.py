import requests
import dateutil.parser as dparser
import datefinder
from datetime import datetime
import csv
from concurrent.futures import ThreadPoolExecutor
import pandas


from os import walk
import glob
import os


statusMap = {'Advance Parole Document Was Produced':'Approve',
'Card Destroyed':'Deny',
'Card Was Mailed To Me':'Approve',
'Case Closed Benefit Received By Other Means':'Approve',
'Case Rejected Because I Sent An Incorrect Fee':'Deny',
'Case Rejected For Incorrect Fee And Form Not Signed':'Deny',
'Case Rejected For Incorrect Fee And Incorrect Form Version':'Deny',
'Case Remains Pending':'Active Review',
'Case Was Approved':'Approve',
'Case Was Denied':'Deny',
'Case Was Received':'Not yet Reviewed',
'Case Was Rejected Because I Did Not Sign My Form':'Deny',
'Case Was Rejected Because It Was Improperly Filed':'Deny',
'Case Was Transferred And A New Office Has Jurisdiction':'Active Review',
'Case Was Updated To Show Fingerprints Were Taken':'Not yet Reviewed',
'Date of Birth Was Updated':'Not yet Reviewed',
'Duplicate Notice Was Mailed':'Not yet Reviewed',
'Fees Were Waived':'Not yet Reviewed',
'Name Was Updated':'Not yet Reviewed',
'New Card Is Being Produced':'Approve',
'Notice Was Returned To USCIS Because The Post Office Could Not Deliver It':'Not yet Reviewed',
'Request for Initial Evidence Was Sent':'Active Review',
"Response To USCIS Request For Evidence Was Received":'Active Review',
'Card Was Returned To USCIS':'Deny',
'Case Is On Hold':'Active Review',
'Case is Ready to Be Scheduled for An Interview':'Active Review',
'Case Rejected Because The Version Of The Form I Sent Is No Longer Accepted':'',
'Case Transferred To Another Office':'Active Review',
'Case Was Reopened':'Active Review',
'Correspondence Was Received And USCIS Is Reviewing It':'Active Review',
'Expedite Request Denied':'Deny',
'Fingerprint Fee Was Received':'Not yet Reviewed',
'Form G-28 Was Rejected Because It Was Improperly Filed':'Deny',
'Interview Was Completed And My Case Must Be Reviewed':'Active Review',
'Interview Was Rescheduled':'Active Review',
'Interview Was Scheduled':'Active Review',
"Notice Explaining USCIS' Actions Was Mailed":'Deny',
'Petition/Application Was Rejected For Insufficient Funds':'Deny',
'Primary And Ancillary Benefits Were Denied':'Deny',
'Request for Additional Evidence Was Sent':'Active Review',
'Request for Additional Information Received':'Active Review',
'Request for Initial and Additional Evidence Was Mailed':'Active Review',
"Response To USCIS' Request For Evidence Was Received":'Active Review'
}



def getData(receiptNum):
    receiptNumber = ''
    formNum = ''
    actionCodeText = ''
    actionCodeDesc = ''
    status = ''
    date = ''
    today = datetime.today().strftime('%Y-%m-%d')
    i = 0
    while True:
        try:
            url = 'https://egov.uscis.gov/csol-api/ui-auth/' + receiptNum

            headers = {'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,ja;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'egov.uscis.gov',
            'Referer': 'https://egov.uscis.gov/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'}

            response = requests.get(url,headers=headers)
            authToken = 'Bearer ' + response.json()['JwtResponse']['accessToken']

            url1 = 'https://egov.uscis.gov/csol-api/case-statuses/' + receiptNum

            headers1 = {'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,ja;q=0.6',
            'Authorization':authToken,
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'egov.uscis.gov',
            'Referer': 'https://egov.uscis.gov/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'}


            response1 = requests.get(url1, headers=headers1)

            json = response1.json()

            receiptNumber = json["CaseStatusResponse"]["receiptNumber"]
            if bool(json["CaseStatusResponse"]['isValid']):       
                formNum = json["CaseStatusResponse"]["detailsEng"]["formNum"]
                actionCodeText = json["CaseStatusResponse"]["detailsEng"]["actionCodeText"]
                actionCodeDesc = json["CaseStatusResponse"]["detailsEng"]["actionCodeDesc"]
                matches = datefinder.find_dates(actionCodeDesc)
                for match in matches:
                    date = match.strftime('%Y-%m-%d')
                    break
        except Exception as e:
            print(i, '::',receiptNum,'::',e)
            i += 1
            if i < 4:
                continue
        break
    
        
    dict = {
        'receiptNumber':receiptNumber,
        'formNum':formNum, 
        'status':statusMap.get(actionCodeText),
        'actionCodeText':actionCodeText, 
        'lastUpdateDate':date,
        'today':today
    }
    print(dict)
    return dict


def callToday():
    filename = '/Users/wen/Documents/uscis/data'+ datetime.today().strftime('%Y-%m-%d-%H-%M') + '.csv'
    fields = ['receiptNumber', 'formNum', 'actionCodeText', 'status', 'lastUpdateDate','today']

    data = {}
    startReceipt = 'MSC249044'
    receiptAarry = []

    for i in range(0,10000):
        receiptAarry.append(startReceipt+str(i).zfill(4))

    result =[]
    with ThreadPoolExecutor(max_workers=64) as exe:
        result = exe.map(getData,receiptAarry)

    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        
            # writing headers (field names)
        writer.writeheader()

        # writing data rows
        for r in result:
            writer.writerow(r)

def generarteReport():

    print('\n\n\n\n\nToday is: ', datetime.today().strftime('%Y-%m-%d'),'\n\n\n')

    path = '/Users/wen/Documents/uscis/'
    all_files = glob.glob(os.path.join(path, "*.csv"))

    dp = pandas.concat((pandas.read_csv(f) for f in all_files), ignore_index=True)

    table1 = pandas.pivot_table(dp[dp.formNum == 'I-485'], values='receiptNumber', index=['status', 'actionCodeText'], columns=['formNum', 'today'], aggfunc="count", fill_value=0)
    
    dp1 = dp.dropna()[(dp.dropna().lastUpdateDate == dp.dropna().today)]
    #datetime.today().strftime('%Y-%m-%d'))]

    table2 = pandas.pivot_table(dp1[dp1.formNum == 'I-485'], values='receiptNumber', index=['status', 'actionCodeText'], columns=['formNum', 'today'], aggfunc="count", fill_value=0)
    
    table3 = pandas.pivot_table(dp[dp.formNum == 'I-485'], values='receiptNumber', index=['status'], columns=['formNum', 'today'], aggfunc="count", fill_value=0)

    print(table1)
    print(table2)
    print(table3)

    print(dp.dropna()[(dp.dropna().formNum == 'I-485') 
    & (dp.dropna().lastUpdateDate == datetime.today().strftime('%Y-%m-%d'))].to_string())


    dp3 = (dp.dropna()[(dp.dropna().formNum == 'I-485') 
    & (dp.dropna().today == datetime.today().strftime('%Y-%m-%d'))]
    )
    
    dp3['receiptNumberShort'] = dp3['receiptNumber'].str[:-3]
    tablex = pandas.pivot_table(dp3, values='today', index=['receiptNumberShort'], columns=['status'], aggfunc="count", fill_value=0)

    print(tablex.to_string())

t = datetime.today()
callToday()
generarteReport()
print((datetime.today())- t)
