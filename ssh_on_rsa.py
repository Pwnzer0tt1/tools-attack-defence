from http import server
import os, time, secrets
from pwn import *
from datetime import datetime
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

def time_filename(filename):
    now = datetime.now() # current date and time
    data = now.strftime(".%d.%m.%Y.%H.%M.%S")
    return filename + data

def write_file(filename, content):
    if os.path.exists(filename): 
        os.rename(filename, time_filename(filename))
    with open(filename, 'bw') as file:
        file.write(content)

def gen_key():
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048
    )

    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.PKCS8,
        crypto_serialization.NoEncryption()
    )

    public_key = key.public_key().public_bytes(
        crypto_serialization.Encoding.OpenSSH,
        crypto_serialization.PublicFormat.OpenSSH
    )

    return public_key, private_key

initial_path = os.path.abspath(os.getcwd())

#Paramethers
ssh_ip = args.IP
psw = args.PSW
port = int(args.PORT) if args.PORT else 22 
auth_key = args.AUTHKEYS
server_private_key = args.SERVER_PRIVATE_KEY


#Paramther validation
assert ssh_ip, 'IP non valido'
assert psw, 'Password non inserita'
if auth_key: assert os.path.isfile(auth_key), "auth_key file path is not valid"
if server_private_key: assert os.path.isfile(server_private_key), "server private key path is invalid"
#---

os.chdir(os.path.expanduser('~'))

try:    
    os.mkdir('.ssh')
except FileExistsError as e:
    assert not os.path.isdir('~/.ssh')

os.chdir('.ssh')

if not auth_key:
    public, private = gen_key()
    write_file('id_rsa.pub', public)
    write_file('id_rsa', private)
    os.chmod('id_rsa', 0o400) # -r--------
    log.info('RSA keys generated!')

while True:
    try:
        connection = ssh("root", host=ssh_ip, port=port, password=psw, ignore_config=True)
        break
    except Exception:
        #traceback.print_exc()
        time.sleep(1)
    
connection('''
mkdir -m 0700 -p /root/.ssh 2> /dev/null;
touch /root/.ssh/authorized_keys
''')

tmp_filename = secrets.token_hex(16)
if auth_key:
    connection.put(os.path.join(initial_path,auth_key),f"/tmp/{tmp_filename}")
else:
    connection.upload_data(public, f"/tmp/{tmp_filename}")

connection(f'''
cat /tmp/{tmp_filename} >> /root/.ssh/authorized_keys;
chmod 600 /root/.ssh/authorized_keys;
sudo mv /etc/ssh/sshd_config /etc/ssh/{time_filename('sshd_config')};
''')

connection.upload_data(b''' 
PermitRootLogin yes
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding yes
PrintMotd no
AcceptEnv LANG LC_*
''', '/etc/ssh/sshd_config')

connection('sudo service ssh reload')

#Change password
password = secrets.token_hex(16)
log.info(f'Password: {password}')
connection(f'echo -e "{password}\n{password}" | passwd root')

#Server private key upload
if server_private_key:
    connection.put(os.path.join(initial_path,server_private_key), '/root/.ssh/id_rsa')
    connection("chmod 400 /root/.ssh/id_rsa")

#End
connection.close()