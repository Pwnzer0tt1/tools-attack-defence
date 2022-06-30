#!/usr/bin/env python3
import argparse, os, yaml, shutil
from time import sleep
from firegexapi import FiregexAPI

pref = "\033["
reset = f"{pref}0m"

class colors:
    black = "30m"
    red = "31m"
    green = "32m"
    yellow = "33m"
    blue = "34m"
    magenta = "35m"
    cyan = "36m"
    white = "37m"

def puts(text, *args, color=colors.white, is_bold=False, **kwargs):
    print(f'{pref}{1 if is_bold else 0};{color}' + text + reset, *args, **kwargs)

def sep(): puts("-----------------------------------", is_bold=True)

parser = argparse.ArgumentParser()
parser.add_argument("--address", "-a", type=str , required=False, help='Address of firegex backend', default="http://127.0.0.1:4444/")
parser.add_argument("--service_name", "-n", type=str , required=False, help='Name of the test service', default=os.path.split(os.getcwd())[-1])
parser.add_argument("--password", "-p", type=str, required=True, help='Firegex password')
args = parser.parse_args()

sep()
puts(f"Connecting to ", color=colors.cyan, end="")
puts(f"{args.address}", color=colors.yellow)


firegex = FiregexAPI(args.address)
service_created = False

#Connect to Firegex
if (firegex.get_status() == "init"):
    if (firegex.set_password(args.password)): puts(f"Sucessfully logged in ✔", color=colors.green)
    else: puts(f"Test Failed: Unknown response or wrong passowrd ✗", color=colors.red); exit(1)
else:
    if (firegex.login(args.password)): puts(f"Sucessfully logged in ✔", color=colors.green)
    else: puts(f"Test Failed: Unknown response or wrong passowrd ✗", color=colors.red); exit(1)

#Read docker-compose.yaml
shutil.copyfile("docker-compose.yml","docker-compose.yml.old")
config = {}
with open("docker-compose.yml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
        if not "services" in config: raise Exception("No services found")
        for service_name, serv_config in config["services"].items():
            if "ports" in serv_config:
                for port_id,port in enumerate(serv_config["ports"]):
                    port_array = port.split(":")
                    if len(port_array) < 1 or len(port_array) > 3 : raise Exception("Invalid port array")
                    if len(port_array) == 2:
                        ipaddr = "0.0.0.0"
                        hostport,containerport = port_array
                    else:
                        ipaddr,hostport,containerport = port_array
                    hostport = int(hostport)

                    name = f"{args.service_name} {service_name}"
                    if len(serv_config["ports"]) > 1:
                        name += hostport
                    if not firegex.create_service(name,hostport):raise Exception("Coudln't create service")
                    
                    service = firegex.get_service_details(args.service_name)
                    if not service : raise Exception("Service on firegex not found")
                    internal_port = service["internal_port"]
                    service_id = service["id"]
                    config["services"][service_name]["ports"][port_id] = f"127.0.0.1:{internal_port}:{containerport}"

                    if(firegex.start(service_id)): 
                        puts(f"Sucessfully started service with id {name} ✔", color=colors.green)
                    else: raise Exception(f"Error while starting service {name}")

 
    except Exception as e:
        print(e)
        os.remove("docker-compose.yml")
        shutil.copyfile("docker-compose.yml.old","docker-compose.yml")
        exit(1)

with open("docker-compose.yml", "w") as stream:
    stream.write(yaml.dump(config))
    pass

os.system("docker-compose up -d --build")
