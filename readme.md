# XIQ PPSK Password Reset
### PPSK_password_reset.py
## Purpose
This script will change the password for PPSK users by adding a 1 to the end of the password, then change the password back to the original password. This is a found workaround for an issue found with 25r1 release were PPSK users are unable to authenticate. 
>NOTE: CFD-13350

## Information
The script can be ran against all PPSK user, or you can select a specific user group to run it against.
If there are users that were done manually, or you do not want to reset the password, you can add a list of users to the exclude.txt file. One user per line. The user name must match exactly what is in XIQ.

If the script stops for any reason, you can copy the output of the script in the exclude.txt file and it will parse the completed users from the 'Updating User {username}... Success' lines in addition to any user name entered. User names will not be parsed from any other strings.
>NOTE: Each user will receive emails for the password change if deliver password is enabled for the users! One with the 1 at the end and one with the original password. They may not receive the emails in the correct order!

The script will collect the PPSK users and present the count of users found. You can acknowledge before making any changes to the users.

```
-- There were 2902 PPSK users found. --
** If script is stopped and started again, all users will be changed again.
Would you like to reset passwords for these users? (y/n) 
```
>Note: This will not account for users in the exclude list. 

As the script runs against the users, if the user name is found in the exclude.txt file a message will be shown like this.
```
[--] Skipping user User1718 Lastname found in exclude.txt
[--] Skipping user User1720 Lastname found in exclude.txt
```
## Needed Files
The script uses other files. If these files are missing the script will not function. 
In the same folder as the script, there should be an ../app/ folder. This folder will contain additional scripts, xiq_api.py and logger.py
In the same folder as the script, there should be a exclude.txt file. This can be left empty if you users are to be excluded.

## Running the script
open the terminal to the location of the script and run this command.
```
python PPSK_password_reset.py
```
You will be presented with a prompt to login in with your XIQ credentials. The password will not be visible. 

>Note: You can add a token in the script if you do not want to enter credentials. Enter the token on line 16.

You will then be asked if you would like to filter on a user group.
```
[OK] User ******** logged in
Would you like to run this script against a particular user group? (y/n)
```
If you enter 'y' or 'yes' the script will prompt for a user group name. Once entered the script will search XIQ for that user group. If found, the script will proceed to collect PPSK users belonging to that user group.

If you enter 'n' or 'no' the script will proceed to collect all PPSK users.

As mentioned above, once the PPSK users are collected, the script will prompt with the count of users found allowing you to proceed to make the changes or not. 

If you proceed, the script will output a line for each user so you can view what is happening. 

```
[--] Skipping user User1809 Last found in exclude.txt
Updating User User1810 Last... Success
[--] Skipping user User1786 Last found in exclude.txt
Updating User User1811 Last... Success
[--] Skipping user User1791 Last found in exclude.txt
Updating User User1812 Last... Success
Updating User User1813 Last... Success
Updating User User1815 Last... Success
```
Once the script has finished updating all users the script will show the following prompt and then exit.
```
[OK] Completed the Users
[OK] Goodbye!
```

## Requirements
The requests module is need for this script.  
All needed modules are listed in the requirements.txt file and can be installed with the 'pip install -r requirements.txt' if pip is used.