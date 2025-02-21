#!/usr/bin/env python3
import re
import sys
import time
import logging
import getpass
from app.xiq_api import XIQ, APICallFailedException
from app.logger import logger
logger = logging.getLogger('PPSK_Password_reset.Main')

VERSION = "v1.0"

#Global Variables
excludeFilename = 'exclude.txt'

token = ''  # can add an API token to bypass XIQ login
x = None # Used for XIQ Session

def prgood(content):
    # print(f"[\033[0;32m✓\033[0m] {content}")
    # so that people aren't confused by the [?]
    print(f"[\033[0;32mOK\033[0m] {content}")

def prbad(content):
    print(f"[\033[0;91mXX\033[0m] {content}")

def prinfo(content):
    print(f"[--] {content}")

def exitOnEnter(errCode = 0):
    input("[--] Press Enter to exit...")
    exit(errCode)
    # 1 - user failed to log in
    # 2 - error retrieving PPSK users
    # 3 - exit after user change failed

def yesNoLoop(question):
    validResponse = False
    while validResponse != True:
        response = input(f"{question} (y/n) ").lower()
        if response =='n' or response == 'no':
            response = 'n'
            validResponse = True
        elif response == 'y' or response == 'yes':
            response = 'y'
            validResponse = True
        elif response == 'q' or response == 'quit':
            exitOnEnter(errCode=0)
    return response


def login():
    ## Login 
    global x
    XIQ_username = input('Email: ')
    XIQ_password = getpass.getpass('Password: ')
    if XIQ_username and XIQ_password:
        x = XIQ(user_name=XIQ_username, password=XIQ_password)
    else:
        print("username or password was not entered")
        exitOnEnter(errCode=1)
    prgood(f"User {XIQ_username} logged in")
    time.sleep(2)

def getUserGroupId(groupName):
    validGroup = False
    while not validGroup:
        user_group_list = x.getUserGroups()
        # Use a generator expression to find the first match
        matched_group = next((user_group for user_group in user_group_list if groupName in user_group), None)

        if matched_group:
            validGroup = True
            prgood(f"User group {groupName} found.")
            return(matched_group[groupName])
        else:
            prinfo(f"{groupName} not found in any user group.")
            response = yesNoLoop("Would you like to search again?")
            if response == 'n':
                exitOnEnter(0)
            else:
                groupName = input("Enter the user group name: ")



# Function to extract names from lines
def extract_name(line):
    match = re.search(r'Updating\sUser\s(.+?)\.\.\.\sSuccess', line)
    if match:
        return match.group(1)
    return line

def importExclude(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()

    # Extract names from each line
    names = [extract_name(line) for line in lines if extract_name(line)]
    return names

### MAIN ###
# check for excluded PPSK users
skip_ppsk_list = importExclude(excludeFilename)

# log into XIQ
if not token:
    print('Enter your XIQ login credentials for the account')
    login()
else:
    x = XIQ(token=token)

# get user group if applicable
user_group_id = None
user_group_response = yesNoLoop("Would you like to run this script against a particular user group?")
if user_group_response == 'y':
    userGroupName = input("Please enter the user group name: ")
    user_group_id = getUserGroupId(userGroupName)

# collect PPSK users
try:
    ppsk_users = x.retrievePPSKUsers(user_group_id)
except APICallFailedException as err:
    logger.error(err)
    print("Failed to collect users.")
    exitOnEnter(2) 
##Prompt user for import confirmation
print(f"\n\033[5;33m-- There were {len(ppsk_users)} PPSK users found. --\033[0m")
print("** If script is stopped and started again, all users will be changed again.")
response = yesNoLoop("Would you like to reset passwords for these users?")
if response == 'n':
    print("\nNo changes will be made.")
    exitOnEnter(0)

for user in ppsk_users:
    if user['user_name'] in skip_ppsk_list:
        prinfo(f"Skipping user {user['user_name']} found in exclude.txt")
        continue
    user_id = user['id']
    user_name = user['user_name']
    password = user['password']
    email = user['email_password_delivery']
    temp_password = f"{password}1"
    print(f"Updating User {user_name}... ", end="")
    sys.stdout.flush()
    # Change user to temp password
    try:
        status = x.updatePPSKUserPassword(user_id,temp_password)
    except APICallFailedException as err:
        logger.error(f"failed to change {user_name} - {user_id} password to temp")
        logger.error(err)
        print("Failed")
        print("** If script is stopped and started again, all users will be changed again. Add users you would like to skip to the exclude.txt file.")
        continueResponse = yesNoLoop("Would you like to continue with other users?")
        if continueResponse == 'n':
            exitOnEnter(3)
        elif continueResponse == 'y':
            prgood("Continuing")
            continue
    time.sleep(2)
    # Change user back to password
    try:
        status = x.updatePPSKUserPassword(user_id,password)
    except APICallFailedException as err:
        logger.error(f"failed to change {user_name} - {user_id} back to password")
        logger.error(err)
        print("Failed")
        print("** If script is stopped and started again, all users will be changed again. Add users you would like to skip to the exclude.txt file.")
        prbad(f"\n\033[5;33m-- USER {user_name} - {user_id} HAS THE TEMP PASSWORD!! (1 added to the end) --\033[0m\n")
        continueResponse = yesNoLoop("Would you like to continue with other users?")
        if continueResponse == 'n':
            exitOnEnter(3)
        elif continueResponse == 'y':
            prgood("Continuing")
            continue
    print("Success")
    sys.stdout.flush()
    logger.info(f"Successfully updated user {user_name} - {user_id}")

prgood("Completed the Users")
prgood("Goodbye!")
time.sleep(2)