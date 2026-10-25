# Library Book Manager: DevOps Mid-Term Lab (CSC418)

A simple 3-tier web app (HTML/CSS front-end, Flask back-end, MySQL database) deployed with
**Docker + Docker Compose** on **AWS EC2** instances behind an **Application Load Balancer**,
managed by an **Auto Scaling Group**, and tested with **Selenium WebDriver**.

```
User/Browser ──► AWS Application Load Balancer (port 80)
                     │  health check: GET /health
          ┌──────────┴──────────┐
     EC2 #1 (AZ-a)          EC2 #2 (AZ-b)        ◄── Auto Scaling Group (min 2, max 4)
   ┌───────────────┐      ┌───────────────┐          launched from a Launch Template
   │ docker compose│      │ docker compose│          whose User Data installs Docker
   │  web :80→5000 │      │  web :80→5000 │          and runs `docker compose up`
   │  db  (MySQL)  │      │  db  (MySQL)  │
   │  vol mysql_data      │  vol mysql_data
   └───────────────┘      └───────────────┘
Selenium (your laptop) ──► ALB DNS name
```

## Project structure

| Path | Purpose |
|---|---|
| `app/app.py` | Flask back-end: routes `/`, `/add`, `/delete/<id>`, `/api/books`, `/health` |
| `app/templates/index.html`, `app/static/style.css` | Front-end |
| `app/Dockerfile` | Builds the custom image `library-web:1.0` |
| `app/requirements.txt` | Python dependencies (pinned versions) |
| `docker-compose.yml` | Two services (`web`, `db`), named volume `mysql_data`, network `backend` |
| `.env.example` | Passwords and settings; copy to `.env` |
| `db/init.sql` | Creates the table and seed data on the first start |
| `scripts/user-data.sh` | EC2 Launch Template user data (auto-install and start) |
| `scripts/linux_admin.sh` | Task 2: Linux commands and permissions |
| `scripts/docker_image_demo.sh` | Task 3: build the image and run a container |
| `scripts/volume_persistence_demo.sh` | Task 4: data survives container recreation |
| `tests/selenium_test.py` | Task 6: Selenium test |

---

## STEP 0: Put the code on GitHub (needed by the Auto Scaling instances)

1. Edit `.env.example`: set `STUDENT=` to your name and registration number.
2. Edit `app/Dockerfile` `LABEL maintainer=` with your name and registration number.
3. Create a **public** GitHub repo called `library-app` and push this folder:
   ```bash
   git init && git add . && git commit -m "DevOps midterm lab"
   git branch -M main
   git remote add origin https://github.com/<you>/library-app.git
   git push -u origin main
   ```
4. In `scripts/user-data.sh`, set `REPO_URL` to your repo URL (commit and push again).

## STEP 1: Security groups (EC2 → Security Groups → Create)

| Name | Inbound rules |
|---|---|
| `alb-sg` | HTTP 80 from `0.0.0.0/0` |
| `web-sg` | HTTP 80 from **source = alb-sg**; SSH 22 from **My IP** |

The EC2 instances accept web traffic only from the load balancer, not directly from the internet. This is good practice.

## STEP 2: One test instance for Tasks 2–5 (manual work and screenshots)

1. Launch an instance: **Amazon Linux 2023**, `t2.micro`/`t3.micro`, your key pair, `web-sg`
   (for this one, also temporarily add HTTP 80 from My IP so you can open it directly).
2. Connect: `ssh -i key.pem ec2-user@<public-ip>` (or EC2 Instance Connect).
3. **Install Docker manually** (Task 3):
   ```bash
   sudo dnf update -y
   sudo dnf install -y docker git
   sudo systemctl enable --now docker
   sudo usermod -aG docker ec2-user      # then log out and back in
   sudo mkdir -p /usr/local/lib/docker/cli-plugins
   sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m) \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
   sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
   docker --version && docker compose version
   ```
4. Get the code: `sudo git clone https://github.com/<you>/library-app.git /opt/library-app && sudo chown -R ec2-user /opt/library-app && cd /opt/library-app`
5. Run the demos and screenshot each one:
   ```bash
   bash scripts/linux_admin.sh              # Task 2
   bash scripts/docker_image_demo.sh        # Task 3
   cp .env.example .env && chmod 600 .env
   docker compose up -d --build             # Task 5
   docker compose ps
   docker network ls && docker network inspect library_backend
   docker exec library-web python -c "import socket;print(socket.gethostbyname('db'))"   # service discovery
   bash scripts/volume_persistence_demo.sh  # Task 4
   ```
6. Open `http://<public-ip>` in your browser and take a screenshot.

## STEP 3: Launch Template (EC2 → Launch Templates → Create)

* Name `library-lt`, AMI **Amazon Linux 2023**, type `t2.micro`/`t3.micro`, key pair, security group `web-sg`
* **Advanced details → User data**: paste the whole of `scripts/user-data.sh` (with your REPO_URL)

## STEP 4: Target Group (EC2 → Target Groups → Create)

* Type **Instances**, name `library-tg`, protocol HTTP, port **80**, your default VPC
* Health check path **`/health`**. Under advanced settings: healthy threshold 2, interval 15s.
* **Do not register any targets.** The Auto Scaling Group will register them.

## STEP 5: Application Load Balancer (EC2 → Load Balancers → Create → ALB)

* Name `library-alb`, **Internet-facing**, IPv4
* Network mapping: choose **at least 2 Availability Zones** (subnets)
* Security group: `alb-sg` (remove `default`)
* Listener **HTTP:80 → forward to `library-tg`**

## STEP 6: Auto Scaling Group (EC2 → Auto Scaling Groups → Create)

1. Name `library-asg`, launch template `library-lt`
2. VPC: the **same 2+ subnets/AZs** as the ALB
3. Load balancing: **Attach to an existing load balancer → `library-tg`**,
   tick **Turn on Elastic Load Balancing health checks**, grace period 300s
4. Group size: **Desired 2, Min 2, Max 4**
5. Scaling policy: **Target tracking**, metric *Average CPU utilization*, target **50**
6. Create, then wait about 5–7 minutes (user data installs Docker and starts the containers)

## STEP 7: Verify and demonstrate

* **Target Groups → library-tg → Targets**: 2 targets **healthy** (screenshot this)
* Copy the **ALB DNS name** (e.g. `library-alb-123.us-east-1.elb.amazonaws.com`) and open
  `http://<DNS>` in a browser. Refresh a few times: the **EC2 instance ID** on the page
  changes, which shows the load balancing.
* **Auto Scaling demo (self-healing):** terminate one instance in the EC2 console. The ASG's
  *Activity* tab shows that it launches a replacement to keep 2 instances.
* **Scale-out demo (optional):** SSH into an instance and run
  `sudo dnf install -y stress-ng && stress-ng --cpu 2 --timeout 600`. After a few minutes the CPU
  alarm fires and the ASG adds an instance. Or simply edit **Desired capacity → 3**.

## STEP 8: Selenium test (from your laptop)

```bash
cd tests
pip install -r requirements.txt          # needs Google Chrome installed
python selenium_test.py http://<ALB-DNS-name>
```
Selenium 4.6+ downloads the right ChromeDriver automatically. Screenshots are saved in `tests/screenshots/`.

## Clean-up after the viva (to stop charges)

Delete in this order: **ASG** (this terminates its instances) → **ALB** → **Target Group** → **Launch Template** →
test instance. Keep everything running until the viva is done.

## Useful commands

```bash
docker compose ps                 # container status
docker compose logs -f web        # web logs
docker compose down               # stop and remove containers (volume kept)
docker compose down -v            # also delete the volume (data lost!)
docker volume inspect library_mysql_data
sudo cat /var/log/user-data.log   # did the launch script work on an ASG instance?
```
