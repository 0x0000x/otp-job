API Notes EN
1. Document Purpose
This document describes the current API structure, request parameters, and response examples.

2. API Overview
GET /status: status check, used to confirm the service is available
POST /api/v1/users/info: view the current user's basic information
POST /api/v1/projects/{project_id}/numbers/upload: upload phone numbers
POST /api/v1/projects/{project_id}/otp/upload: upload OTP codes
POST /api/v1/projects/{project_id}/numbers/info: view a single phone number
POST /api/v1/projects/{project_id}/numbers/list: view a paginated number list
3.Common Request Rules
All business APIs require these fields in the JSON body:

uid
api_token
Headers:

Content-Type: application/json
Domain note:

the base_url in this document is only a placeholder and is not a real service address
for the actual request domain, please contact online customer support
Minimal integration steps:

Prepare a valid uid
Prepare the matching api_token
Call GET /status to confirm the service is available
Call the number upload API
After a number is uploaded successfully, call the OTP upload API
If needed, call the number info API to view the current number details
If needed, call the user basic info API to view wallet and statistic fields for the current uid
If needed, call the number list API to paginate through existing records
Python requests example:

import requests

base_url = "https://your-api-domain.example"
project_id = "1"

payload = {
    "uid": "10001",
    "api_token": "your_api_token_here",
    "code_type": "sms",
    "ccnum_list": [
        "8801712345678",
        "254712345678"
    ]
}

response = requests.post(
    f"{base_url}/api/v1/projects/{project_id}/numbers/upload",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15,
)

print(response.status_code)
print(response.json())
4. Common Response Format
Success example:

{
  "status": "succ",
  "data": {}
}
Error example:

{
  "status": "err",
  "tips": "API token is invalid.",
  "data": {
    "error_code": "invalid_api_token"
  }
}
Notes:

status = succ usually does not return tips
status = err returns tips
error tips use short and simple English
Common field notes:

status: request result, succ or err
tips: error message, usually returned only on failure
data: main business payload
data.error_code: error code for program-side handling
5. Endpoint Details
5.1 Status Check
Purpose:

confirm that the service is available
Request:

GET /status
Success example:

{
  "status": "succ",
  "data": {
    "healthy": true,
    "service": "oj_uapi",
    "version": "0.1.0"
  }
}
5.2 View Current User Basic Info
Purpose:

view the basic information of the current uid
mainly returns withdrawable balance, withdrawing amount, total income, and usage statistics
Request:

POST /api/v1/users/info
Python requests example:

import requests

base_url = "https://your-api-domain.example"

payload = {
    "uid": "10001",
    "api_token": "your_api_token_here"
}

response = requests.post(
    f"{base_url}/api/v1/users/info",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15,
)

print(response.status_code)
print(response.json())
Body example:

{
  "uid": "10001",
  "api_token": "your_api_token_here"
}
Field notes:

uid: user id
api_token: API token for the current uid
Key response fields:

data.uid: user id
data.withdrawable_balance: current withdrawable balance, from Redis balance
data.withdrawing_balance: amount currently being withdrawn, from Redis balance_txz
data.withdrawn_balance: amount already withdrawn successfully, from Redis balance_ytx
data.total_income: total income, from Redis m
data.work_income: total work income, from Redis m1
data.promotion_income: total referral commission income, from Redis m2
data.submitted_number_count: total submitted phone numbers, from Redis count_num
data.submitted_otp_count: total submitted OTPs, from Redis count_code
data.successful_registration_count: total successful registrations, from Redis count_reg_succ
Notes:

amount fields always return as strings with 4 decimal places
count fields always return as integers
if a field is empty in Redis, the API returns 0
Success example:
```
{
  "status": "succ",
  "data": {
    "uid": "10001",
    "withdrawable_balance": "12.5000",
    "withdrawing_balance": "1.2000",
    "withdrawn_balance": "30.0000",
    "total_income": "52.8000",
    "work_income": "40.3000",
    "promotion_income": "12.5000",
    "submitted_number_count": 120,
    "submitted_otp_count": 85,
    "successful_registration_count": 60
  }
}
```
Handling suggestions:

if the API returns status = err, first check whether uid and api_token are correct
if an amount field returns 0.0000, the corresponding Redis field is usually empty or missing
if a count field returns 0, the corresponding statistic usually has no accumulated value yet
5.3 Upload Numbers
Purpose:

upload phone numbers for a project through the API
Request:

POST /api/v1/projects/{project_id}/numbers/upload
Body example:
```
{
  "uid": "10001",
  "api_token": "your_api_token_here",
  "code_type": "sms",
  "ccnum_list": [
    "8801712345678",
    "254712345678"
  ]
}
```
Field notes:

project_id: project id in the URL path
uid: user id
code_type: currently supports sms and app
ccnum_list: list of phone numbers, maximum 20 per request
Key response fields:

data.project_id: project id
data.uid: user id
data.code_type: OTP type used in this request
data.count_succ: number of successful items
data.count_failed: number of failed items
data.items: per-number result list
data.items[].ccnum: phone number
data.items[].success: whether this number was accepted
data.items[].failed_code: failure code, empty on success
data.items[].failed_reason: failure message, empty on success
Success example:

{
  "status": "succ",
  "data": {
    "project_id": "1",
    "uid": "10001",
    "code_type": "sms",
    "count_succ": 1,
    "count_failed": 1,
    "items": [
      {
        "ccnum": "8801712345678",
        "success": true,
        "failed_code": "",
        "failed_reason": ""
      },
      {
        "ccnum": "123456",
        "success": false,
        "failed_code": "101",
        "failed_reason": "This phone number is invalid."
      }
    ]
  }
}
Common failure codes:

101: invalid phone number
102: the number was already used successfully within 30 days
103: the number is still in progress
104: demand for this country is currently satisfied
105: unsupported country or OTP type
202: the number is temporarily unavailable
Handling suggestions:

if you get 101, check the phone number format and country code
if you get 103 or 202, retry later
if you get 104 or 105, try another country or OTP type
if the global submission switch is closed, the whole request returns an error immediately: Number submissions are paused. Please wait a few minutes.
if the project is closed, the API returns an error immediately
if the whole request returns status = err, first check uid, api_token, project_id, and JSON format
5.4 Upload OTP
Purpose:

submit the OTP code for a phone number that was already uploaded
Request:

POST /api/v1/projects/{project_id}/otp/upload
Python requests example:
```
import requests

base_url = "https://your-api-domain.example"
project_id = "1"

payload = {
    "uid": "10001",
    "api_token": "your_api_token_here",
    "ccnum": "8801712345678",
    "code": "123456"
}

response = requests.post(
    f"{base_url}/api/v1/projects/{project_id}/otp/upload",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15,
)

print(response.status_code)
print(response.json())
Body example:

{
  "uid": "10001",
  "api_token": "your_api_token_here",
  "ccnum": "8801712345678",
  "code": "123456"
}
```
Field notes:

project_id: project id in the URL path
uid: user id
ccnum: phone number that was uploaded before
code: digit-only OTP value
Submission requirements:

the number must already exist
the number must belong to the current uid
the project must be open
the current number status must be 1 or 6
status_res = 1: normal OTP submission
status_res = 6: OTP resubmission
status_res meanings:

1: waiting for code, OTP can be submitted
2: submit this number again later, OTP cannot be submitted
3: completed successfully, OTP cannot be submitted
4: this number may be blocked, OTP cannot be submitted
5: this number was banned during registration or transfer, OTP cannot be submitted
6: the OTP was incorrect, OTP can be submitted again
7: OTP was not submitted in time, submit the number again instead of OTP
Key response fields:

data.project_id: project id
data.ccnum: phone number for this OTP
data.code: submitted OTP value
data.code_type: OTP type of the number
data.queued: whether the request has entered the next processing queue
Success example:
```
{
  "status": "succ",
  "data": {
    "project_id": "1",
    "ccnum": "8801712345678",
    "code": "123456",
    "code_type": "sms",
    "queued": true
  }
}
```
Error example:
```
{
  "status": "err",
  "tips": "This number does not belong to the current user.",
  "data": {
    "error_code": "number_owner_mismatch"
  }
}
```
Handling suggestions:

if the API says the number does not exist, confirm that the number was uploaded successfully before
if the API says the number does not belong to the current user, confirm the uid
if the API says OTP format error, confirm that code contains digits only
if the API says the current status does not allow OTP submission, query the current number status first
if the whole request returns status = err, read both tips and data.error_code
5.5 View A Single Number
Purpose:

view the basic information and current status of one phone number
Request:

POST /api/v1/projects/{project_id}/numbers/info
Python requests example:
```
import requests

base_url = "https://your-api-domain.example"
project_id = "1"


payload = {
    "uid": "10001",
    "api_token": "your_api_token_here",
    "ccnum": "8801712345678"
}
```
response = requests.post(
    f"{base_url}/api/v1/projects/{project_id}/numbers/info",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15,
)

print(response.status_code)
print(response.json())
Body example:

{
  "uid": "10001",
  "api_token": "your_api_token_here",
  "ccnum": "8801712345678"
}
Field notes:

project_id: project id in the URL path
uid: user id
ccnum: phone number to query
Key response fields:

data.project_id: project id
data.uid: current owner uid of the number
data.ccnum: phone number
data.country_code: two-letter country code in lowercase; convert it to uppercase if needed
data.price: current user-side price
data.code_type: OTP type, sms or app
data.status_res: current number status code
data.status_text: current number status text
data.status_tone: status color type
data.action_visible: whether the number still has a user-side action state
Success example:

{
  "status": "succ",
  "data": {
    "project_id": "1",
    "uid": "10001",
    "ccnum": "8801712345678",
    "country_code": "bd",
    "price": "0.8000",
    "code_type": "sms",
    "status_res": "1",
    "status_text": "Waiting for Code",
    "status_tone": "blue",
    "action_visible": true
  }
}
Error example:

{
  "status": "err",
  "tips": "This number does not belong to the current user.",
  "data": {
    "error_code": "number_owner_mismatch"
  }
}
Handling suggestions:

if the API says the number does not exist, confirm that the number was uploaded successfully before
if the API says the number does not belong to the current user, confirm that the request uid matches the number owner
if you want to decide whether OTP can be submitted next, first check whether status_res is 1 or 6
5.6 View Number List
Purpose:

view a paginated number list for the current user under one project
Request:

POST /api/v1/projects/{project_id}/numbers/list
Python requests example:

import requests

base_url = "https://your-api-domain.example"
project_id = "1"

payload = {
    "uid": "10001",
    "api_token": "your_api_token_here",
    "list_type": "all",
    "page": 1,
    "page_size": 20
}

response = requests.post(
    f"{base_url}/api/v1/projects/{project_id}/numbers/list",
    json=payload,
    headers={"Content-Type": "application/json"},
    timeout=15,
)

print(response.status_code)
print(response.json())
Body example:

{
  "uid": "10001",
  "api_token": "your_api_token_here",
  "list_type": "all",
  "page": 1,
  "page_size": 20
}
Field notes:

project_id: project id in the URL path
uid: user id
list_type: list type, supports all and suc
page: page number, starting from 1
page_size: page size, maximum 100
if page_size is greater than 100, the API returns an error directly and does not trim it to 100
Key response fields:

data.project_info.project_id: project id
data.project_info.project_name: project name
data.project_info.project_income: accumulated income of the current user in this project
data.list_type: current list type
data.page: current page number
data.page_size: page size
data.total: total records for the current condition
data.total_pages: total page count
data.has_more: whether another page is available
data.items: number records for the current page
Main fields in data.items[]:

ccnum: phone number
price: current user-side price
code_type: OTP type
country_code: two-letter country code in lowercase; convert it to uppercase if needed
status_res: status code
status_text: status text
status_tone: status color type
action_visible: whether the number still has a user-side action state
Success example:
```
{
  "status": "succ",
  "data": {
    "project_info": {
      "project_id": "1",
      "project_name": "Telegram",
      "project_income": "12.5000"
    },
    "list_type": "all",
    "page": 1,
    "page_size": 20,
    "total": 2,
    "total_pages": 1,
    "has_more": false,
    "items": [
      {
        "project_id": "1",
        "uid": "10001",
        "ccnum": "8801712345678",
        "country_code": "bd",
        "price": "0.8000",
        "code_type": "sms",
        "status_res": "1",
        "status_text": "Waiting for Code",
        "status_tone": "blue",
        "action_visible": true
      }
    ]
  }
}
```
Handling suggestions:

list_type=all: view all number records
list_type=suc: view successful numbers
if the page is empty, confirm project_id, uid, and whether this project really has records for the current user