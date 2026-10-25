#!/bin/bash
# ---------------------------------------------------------------------------
# Task 2 - Linux Administration (run on the EC2 instance, as ec2-user)
#   bash scripts/linux_admin.sh
# Each command is printed before it runs, so the output is easy to screenshot.
# ---------------------------------------------------------------------------
run() { echo -e "\n\$ $*"; eval "$@"; }

echo "===== 1. System information ====="
run whoami                     # current user
run hostname                   # machine name
run uname -a                   # kernel / OS info
run cat /etc/os-release \| head -3
run uptime                     # how long the server has been running
run df -h /                    # disk usage
run free -m                    # memory usage (MB)
run pwd                        # current directory

echo -e "\n===== 2. Create a directory structure ====="
run mkdir -p ~/devops-lab/{app,logs,backups}
run touch ~/devops-lab/app/config.txt ~/devops-lab/logs/app.log ~/devops-lab/backups/run.sh
run 'echo "APP_ENV=production" > ~/devops-lab/app/config.txt'
run 'echo "#!/bin/bash" > ~/devops-lab/backups/run.sh; echo "echo backup done" >> ~/devops-lab/backups/run.sh'
run ls -lR ~/devops-lab

echo -e "\n===== 3. File permissions ====="
run chmod 750 ~/devops-lab                   # rwx r-x ---  owner full, group read/enter, others none
run chmod 640 ~/devops-lab/app/config.txt    # rw- r-- ---  owner read/write, group read
run chmod 600 ~/devops-lab/logs/app.log      # rw- --- ---  owner only
run chmod u+x ~/devops-lab/backups/run.sh    # symbolic mode: add execute for the owner
run ls -l ~/devops-lab ~/devops-lab/app ~/devops-lab/logs ~/devops-lab/backups
run stat -c "'%A %a %U:%G %n'" ~/devops-lab/app/config.txt
run ~/devops-lab/backups/run.sh              # executes because of u+x

echo -e "\n===== 4. Ownership ====="
run sudo chown ec2-user:docker ~/devops-lab/logs/app.log   # change owner:group
run ls -l ~/devops-lab/logs

echo -e "\n===== 5. Processes, network and services ====="
run ps aux --sort=-%mem \| head -5           # top memory processes
run sudo ss -tlnp \| grep -E "':80|:22'"     # which ports are listening
run systemctl is-active docker               # is the Docker service running
run id                                       # user + groups (docker group)
echo -e "\nDone."
