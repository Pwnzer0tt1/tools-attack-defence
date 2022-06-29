#!/bin/bash
if [[ "$#" -ne 1 ]]; then
	echo "Usage: ./setup_tools.sh <game_server_ip_addr>"
	exit 2
fi
# Clone tools
#git clone git@github.com:Pwnzer0tt1/firegex.git
#git clone git@github.com:Pwnzer0tt1/tools-attack-defence.git
#git clone git@github.com:Pwnzer0tt1/DestructiveFarm.git
#git clone git@github.com:eciavatta/caronte.git

# Zip all files
#cp tools-attack-defence/caronte.sh caronte.sh
#cp tools-attack-defence/gitbackup.py gitbackup.py
#zip -r ad_tools.zip firegex caronte.sh gitbackup.py
#rm caronte.sh
#rm gitbackup.py

# Copy files
#scp ad_tools.zip root@$1:/root
#rm ad_tools.zip
#ssh root@$1 mkdir tools
#ssh root@$1 apt install -y tmux unzip
#ssh root@$1 unzip ad_tools.zip -d tools
#ssh root@$1 rm ad_tools.zip
#ssh root@$1 mv tools/gitbackup.py gitbackup.py 

# Destructive Farm
cd DestructiveFarm/server
python3 -m pip install -r requirements.txt
cd ..
cd ..

# caronte
cd caronte/

# Build caronte
sudo docker-compose up -d --build
cd ..

# Expose caronte with ngrok
ngrok http 3333 > /dev/null &

# Wait for ngrok to be available
while ! nc -z localhost 4040; do
  sleep 0.2 # wait Ngrok to be available
done

# Get ngrok dynamic URL from its own exposed local API
NGROK_REMOTE_URL="$(curl http://localhost:4040/api/tunnels | jq ".tunnels[1].public_url")"
echo $NGROK_REMOTE_URL
if test -z "${NGROK_REMOTE_URL}"
then
  echo "❌ ERROR: ngrok doesn't seem to return a valid URL (${NGROK_REMOTE_URL})."
  exit 1
fi

# Trim double quotes from variable
NGROK_REMOTE_URL=$(echo ${NGROK_REMOTE_URL} | tr -d '"')
# If https protocol is returned, replace by http
NGROK_REMOTE_URL=${NGROK_REMOTE_URL/https:\/\//http:\/\/}

bold=$(tput bold)
normal=$(tput sgr0)
echo ${NGROK_REMOTE_URL} | tr -d '\n' | xclip -sel clip
printf "\n\n🌍 Your ngrok remote URL is 👉 ${bold}${NGROK_REMOTE_URL} 👈\n📋 ${normal} I've copied it in your clipboard ;) \n\n"

xdg-open ${NGROK_REMOTE_URL}

# Run caronte.sh
NGROK_REMOTE_URL=$(echo ${NGROK_REMOTE_URL} | tr -d 'http://')
ssh root@$1 chmod +x tools/caronte.sh
ssh root@$1 tmux new-session -s caronte "tmux detach;./tools/caronte.sh 45 ${NGROK_REMOTE_URL} game"
config_json = '{"config":{"server_address":"'$1'","flag_regex":"[A-Z0-9]{31}=","auth_required":false},"accounts":{}}'

curl -X POST "http://${NGROK_REMOTE_URL}/api/setup" \
    -H "Content-Type: application/json" \
    -d $config_json

ssh root@$1 python3 ./tools/firegex/start.py

ssh root@$1 find . -maxdepth 1 -name "docker-compose.yml" | xargs dirname | xargs cp gitbackup.py
ssh root@$1 find . -maxdepth 1 -name "docker-compose.yml" | xargs dirname | xargs cp tools/self-combust/* 

ssh root@$1 find . -maxdepth 1 -name "docker-compose.yml" | xargs dirname | xargs -i{} python3 {}/gitbackup.py init -a Pwnzer0tt1 -r cc2022-ad 
ssh root@$1 find . -maxdepth 1 -name "docker-compose.yml" | xargs dirname | xargs -i{} python3 {}/self-combust.py -p ccit-poliba2032
ssh root@$1 find . -maxdepth 1 -name "docker-compose.yml" | xargs dirname | xargs -i{} python3 {}/gitbackup.py commit
