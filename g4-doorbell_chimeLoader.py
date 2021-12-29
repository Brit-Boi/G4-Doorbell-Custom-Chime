# unifi-g4_chimeLoader.py
# Checks for existing uploaded files to doorbell. If they don't exist, upload them

#Imports
from netmiko import ConnectHandler, SCPConn
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
import argparse
import getpass

#Initialize argument parser
parser = argparse.ArgumentParser(description="Checks if custom chime is on given doorbell IP address, and uploads if necessary.")

#Help prompts
ipPrompt = "Set IP address to log in to"
userPrompt = "Set username to log in with (Default: ubnt)"
passPrompt = "Set password to log in with"
filePrompt = "WAV file to upload to doorbell. Specifications can be found in README.md"
resetPrompt = "Reset doorbell chime settings back to default"

#Add optional arguments
#If -r is given, its value is set to true, used later in ifs
# - [NOT TESTED]
parser.add_argument("-r", "--Reset", help = resetPrompt, action='store_true')
parser.add_argument("-a", "--Address", help = ipPrompt)
parser.add_argument("-u", "--Username", help = userPrompt)
parser.add_argument("-p", "--Password", help = passPrompt)
parser.add_argument("-f", "--File", help = filePrompt)

#Read arguments from command line
args = parser.parse_args()

#If read arguments contain information, use those
if bool(args.Address) and bool(args.Username) and bool(args.Password) and bool(args.File):
    ipAddress = args.Address
    username = args.Username
    password = args.Password
    file = args.File
#Otherwise, ask
else:
    ipAddress = input(ipPrompt + "\n")
    username = input("\n" + userPrompt + "\n")
    if username == "":
        username = "ubnt"
    password = getpass.getpass("\n" + passPrompt + "\n")
    #If reset flag is true, don't ask for file
    if bool(args.Reset) == False:
        file = input("\n" + filePrompt + "\n")

#Function that checks for existing file
#Returns bool
def CheckConfig(givenIP, givenUsername, givenPassword, givenFile):
    #Device configuration
    device = {
        'device_type': 'linux',
        'ip': givenIP,
        'username': givenUsername,
        'password': givenPassword
    }

    #Connect to host
    try:
        print("Checking for file...\n")
        net_connect = ConnectHandler(**device)
        output = net_connect.send_command("ls | grep " + file)

        net_connect.disconnect()
        if output == file:
            return True
        else:
            return False

    except(NetMikoTimeoutException):
        print("\n> Timeout connecting to " + givenIP)
        print("\nExiting...")
        exit()
    except(NetMikoAuthenticationException):
        print("\n> Error authenticating to " + givenIP)
        print("\nExiting...")
        exit()
    except():
        print("\n> General error...")
        print("\nExiting...")
        exit()

def SendFile(givenIP, givenUsername, givenPassword, givenFile):
    #Device configuration
    device = {
        'device_type': 'linux',
        'ip': givenIP,
        'username': givenUsername,
        'password': givenPassword
    }

    try:
        print("\n> Connecting to host " + givenIP)
        net_connect = ConnectHandler(**device)
        scp_conn = SCPConn(net_connect)

        #Transfer file to default directory of /etc/persistent
        print("\n> Transferring file to host " + givenIP)
        scp_conn.scp_transfer_file(file, file)

        #Create backup of existing chime.wav file
        print("\n> Creating backup of /etc/sounds/chime.wav")
        net_connect.send_command("mv /etc/sounds/chime.wav /etc/sounds/chime.wav.bak")

        #Create symlink of uploaded file to /etc/sounds/chime.wav
        print("\n> Creating symlink of uploaded file to /etc/sounds/chime.wav")
        net_connect.send_command("ln -s /etc/persistent/" + file + " /etc/sounds/chime.wav")

        print("\n> All done! Disconnecting...")
        net_connect.disconnect()

    except(NetMikoTimeoutException):
        print("\n> Timeout connecting to " + givenIP)
        print("\nExiting...")
        exit()
    except(NetMikoAuthenticationException):
        print("\n> Error authenticating to " + givenIP)
        print("\nExiting...")
        exit()
    except():
        print("\n> General error...")
        print("\nExiting...")
        exit()

#Resets doorbell's config to defaults
def ResetConfig(givenIP, givenUsername, givenPassword):
    #Device configuration
    device = {
        'device_type': 'linux',
        'ip': givenIP,
        'username': givenUsername,
        'password': givenPassword
    }

    try:
        print("\n> Connecting to host " + givenIP)
        net_connect = ConnectHandler(**device)
        scp_conn = SCPConn(net_connect)

        #Create backup of existing chime.wav file
        print("\n> Restoring chime.wav backup")
        net_connect.send_command("mv /etc/sounds/chime.wav.bak /etc/sounds/chime.wav")

        print("\n> All done! Disconnecting...")
        net_connect.disconnect()

    except(NetMikoTimeoutException):
        print("\n> Timeout connecting to " + givenIP)
        print("\nExiting...")
        exit()
    except(NetMikoAuthenticationException):
        print("\n> Error authenticating to " + givenIP)
        print("\nExiting...")
        exit()
    except():
        print("\n> General error...")
        print("\nExiting...")
        exit()

#If -r flag was not present, run either CheckConfig() or SendFile()
if bool(args.Reset) == False:
    #Run 'checkConfig' function to check for file
    #If it returns a true boolean, run 'setConfig'+
    #If it returns false, print message to terminal
    if bool(CheckConfig(ipAddress, username, password, file)):
        #Tell user the doorbell is all set
        print("The doorbell already has the given file, exiting...")
        #Exit gracefully
        exit()
    else:
        #Copy file to doorbell
        SendFile(ipAddress, username, password, file)
#If -r flag was present, run ResetConfig()
# - [NOT TESTED]
else:
    ResetConfig(ipAddress, username, password)