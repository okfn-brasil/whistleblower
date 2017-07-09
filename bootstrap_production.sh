# Configure SSH access
# source: https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-16-04
#
# ----------

useradd -ms /bin/bash serenata_de_amor
git clone --recursive https://github.com/datasciencebr/whistleblower.git /home/serenata_de_amor/whistleblower
chown -hR serenata_de_amor /home/serenata_de_amor/whistleblower

# Setup auto restart services after VM restart
cat >/home/serenata_de_amor/server.sh <<EOL
touch /home/serenata_de_amor/running.txt

sudo -u serenata_de_amor bash << EOF

cd /home/serenata_de_amor/whistleblower
nohup docker-compose up -d --ignore-override

EOF
EOL
(crontab -l ; echo "@reboot /home/serenata_de_amor/server.sh") | sort - | uniq - | crontab -

# Install Docker
# source: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-16-04

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
apt-cache policy docker-ce
sudo apt-get install -y docker-ce
sudo systemctl status docker
sudo usermod -aG docker serenata_de_amor

# Install Docker Compose
# source: https://www.digitalocean.com/community/tutorials/how-to-install-docker-compose-on-ubuntu-16-04
sudo curl -o /usr/local/bin/docker-compose -L "https://github.com/docker/compose/releases/download/1.11.2/docker-compose-$(uname -s)-$(uname -m)"
sudo chmod +x /usr/local/bin/docker-compose

# Missing: .env file and environment-specific docker-compose.yml
