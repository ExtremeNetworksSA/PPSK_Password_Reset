#!/usr/bin/env python3
import logging
import os
import inspect
import sys
import json
import requests
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from requests.exceptions import HTTPError
from app.logger import logger
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger('PPSK_Password_reset.xiq_api')

PATH = current_dir

class APICallFailedException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class XIQ:
    def __init__(self, user_name=None, password=None, token=None):
        self.URL = "https://api.extremecloudiq.com"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.proxyDict = {
            "http": "",
            "https": ""
        }
        if token:
            self.headers["Authorization"] = "Bearer " + token
        else:
            try:
                self.__getAccessToken(user_name, password)
            except ValueError as e:
                print(e)
                raise SystemExit
            except HTTPError as e:
               print(e)
               raise SystemExit
            except:
                log_msg = "Unknown Error: Failed to generate token for XIQ"
                logger.error(log_msg)
                print(log_msg)
                raise SystemExit   
        self.pageSize = 100

    #API CALLS
    def __get_api_call(self, url):
        try:
            rawResponse = requests.get(url, headers= self.headers, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        try:
            response = self.__checkResponse(rawResponse, url)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        return response
    
    def __put_api_call(self, url, payload):
        try:
            rawResponse = requests.put(url, headers= self.headers, data=payload, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        try:
            response = self.__checkResponse(rawResponse, url)
        except APICallFailedException as err:
            raise APICallFailedException(err)
        return response

    def __post_api_call(self, url, payload):
        try:
            rawResponse = requests.post(url, headers= self.headers, data=payload, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        response = self.__checkResponse(rawResponse, url)
        return response
        
    def __delete_api_call(self, url):
        try:
            rawResponse = requests.delete(url, headers= self.headers, verify=False, proxies=self.proxyDict)
        except HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err} - on API {url}')
            raise APICallFailedException(f'HTTP error occurred: {http_err}') 
        response = self.__checkResponse(rawResponse, url)
        return response
    
    def __checkResponse(self, rawResponse, url):
        if rawResponse is None:
            log_msg = "ERROR: No response received from XIQ!"
            logger.error(log_msg)
            raise APICallFailedException(log_msg)
        if rawResponse.status_code != 200:
            log_msg = f"Error - HTTP Status Code: {str(rawResponse.status_code)}"
            logger.error(f"{log_msg}")
            try:
                data = rawResponse.json()
            except json.JSONDecodeError:
                logger.warning(f"\t\t{rawResponse.text}")
            else:
                if 'error_message' in data:
                    logger.warning(f"\t\t{data['error_message']}")
                else:
                    logger.warning(f"\n\n{data}")
            raise APICallFailedException(log_msg) 
        try:
            data = rawResponse.json()
        except json.JSONDecodeError:
            logger.error(f"Unable to parse json data - {url} - HTTP Status Code: {str(rawResponse.status_code)}")
            raise APICallFailedException("Unable to parse the data from json, script cannot proceed")
        return data

    def __getAccessToken(self, user_name, password):
        info = "get XIQ token"
        success = 0
        url = self.URL + "/login"
        payload = json.dumps({"username": user_name, "password": password})
        try:
            data = self.__post_api_call(url=url,payload=payload)
        except APICallFailedException as e:
            print(f"API to {info} failed with {e}")
            print('script is exiting...')
            raise SystemExit
        except:
            print(f"API to {info} failed with unknown API error")
        else:
            success = 1
        if success != 1:
            print("failed to get XIQ token. Cannot continue to import")
            print("exiting script...")
            raise SystemExit
        
        if "access_token" in data:
            #print("Logged in and Got access token: " + data["access_token"])
            self.headers["Authorization"] = "Bearer " + data["access_token"]
            return 0

        else:
            log_msg = "Unknown Error: Unable to gain access token for XIQ"
            logger.warning(log_msg)
            raise ValueError(log_msg)

        
    # External functions
    def retrievePPSKUsers(self, usergroupID=None):
        page = 1
        pageCount = 1
        firstCall = True

        ppskUsers = []

        while page <= pageCount:
            url = f"{self.URL}/endusers?page={str(page)}&limit={str(self.pageSize)}"
            if usergroupID:
                url = f"{url}&user_group_ids={usergroupID}"

            # Get the next page of the ppsk users
            try:
                rawList = self.__get_api_call(url)
            except APICallFailedException as err:
                return APICallFailedException(err)
            ppskUsers = ppskUsers + rawList['data']

            if firstCall == True:
                pageCount = rawList['total_pages']
            print(f"completed page {page} of {rawList['total_pages']} collecting PPSK Users")
            page = rawList['page'] + 1 
        logger.info(f"retrieved {len(ppskUsers)} PPSK users")
        return ppskUsers
    
    def updatePPSKUserPassword(self,userid,password):
        url = f"{self.URL}/endusers/{userid}"
        data = {
            'password': password
        }
        payload = json.dumps(data)
        try:
            response = self.__put_api_call(url, payload)
        except APICallFailedException as err:
            raise APICallFailedException(err)
    
        if response['password'] != password:
            raise APICallFailedException("Failed to change password")
        
        return 0
        

    def getUserGroups(self):
        page = 1
        pageCount = 1
        firstCall = True

        userGroups = []
        while page <= pageCount:
            url = f"{self.URL}/usergroups?page={str(page)}&limit={str(self.pageSize)}"
            # Get the next page of user groups
            try:
                rawList = self.__get_api_call(url)
            except APICallFailedException as err:
                raise APICallFailedException(err)
            userGroups = userGroups + [{ug['name']: ug['id']} for ug in rawList['data']]

            if firstCall == True:
                pageCount = rawList['total_pages']
            print(f"completed page {page} of {rawList['total_pages']} collecting User Groups")
            page = rawList['page'] + 1 
        logger.info(f"retrieved {len(userGroups)} user groups")

        return userGroups