#!/usr/bin/env python3
"""
Deployment script using git clone instead of gh
"""
import sys

try:
    import paramiko
except ImportError:
    pass

# Server configuration
SERVER = "89.116.23.236"
USERNAME = "root"
PASSWORD = "Beeck1337@@@"
PORT = 22

# Deployment commands - using git clone
DEPLOY_COMMANDS = """
set -e
export DEBIAN_FRONTEND=noninteractive
cd /root

echo "=== Current directory ==="
pwd
echo ""

echo "=== Checking if repository exists ==="
if [ -d "YouTube_Farm" ]; then
    echo "Repository exists, updating..."
    cd YouTube_Farm
    git pull origin main 2>/dev/null || echo "Pull completed"
else
    echo "Cloning repository with git..."
    git clone https://github.com/herts444/YouTube_Farm.git
    cd YouTube_Farm
fi

echo ""
echo "=== Repository location ==="
pwd
ls -lah
echo ""

echo "=== Checking .env file ==="
if [ -f .env ]; then
    echo ".env file exists"
else
    echo "Creating .env from template..."
    cp .env.example .env
    echo "WARNING: Configure .env with your credentials!"
fi

echo ""
echo "=== Checking Docker ==="
docker --version 2>/dev/null || echo "Docker not found"
docker-compose --version 2>/dev/null || (docker compose version 2>/dev/null && echo "Using 'docker compose'")

if command -v docker &> /dev/null; then
    # Check for docker-compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        echo "Docker Compose not available!"
        COMPOSE_CMD=""
    fi

    if [ -n "$COMPOSE_CMD" ]; then
        echo ""
        echo "=== Stopping existing containers ==="
        $COMPOSE_CMD down 2>/dev/null || true

        echo ""
        echo "=== Building and starting containers ==="
        $COMPOSE_CMD up -d --build

        echo ""
        echo "=== Waiting for containers... ==="
        sleep 7

        echo ""
        echo "=== Container status ==="
        $COMPOSE_CMD ps

        echo ""
        echo "=== Recent logs (last 40 lines) ==="
        $COMPOSE_CMD logs --tail=40
    fi
else
    echo "Docker not found! Install with: curl -fsSL https://get.docker.com | sh"
fi

echo ""
echo "=============================================  "
echo "  DEPLOYMENT COMPLETE!"
echo "============================================="
"""

def deploy():
    print("=" * 70)
    print("   YouTube Farm - Git Deployment")
    print("=" * 70)
    print(f"\nServer: {SERVER}")
    print(f"User: {USERNAME}")
    print("Connecting...\n")

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(
            hostname=SERVER,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )

        print(f"Connected to {SERVER} as {USERNAME}!")
        print("\nExecuting deployment...\n")
        print("=" * 70)

        stdin, stdout, stderr = ssh.exec_command(DEPLOY_COMMANDS, get_pty=True)

        # Real-time output
        while True:
            line = stdout.readline()
            if not line:
                break
            print(line, end='')

        exit_status = stdout.channel.recv_exit_status()

        print("=" * 70)
        if exit_status == 0:
            print("\nSUCCESS: Deployment completed!")
            print("\nYour bot should now be running on the server!")
        else:
            print(f"\nCompleted with exit code: {exit_status}")

        ssh.close()

        print("\n" + "=" * 70)
        print("Next steps:")
        print(f"1. Configure .env: ssh {USERNAME}@{SERVER}")
        print(f"   cd /root/YouTube_Farm && nano .env")
        print("2. Add your API keys:")
        print("   - TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   - OPENAI_API_KEY=your_openai_key")
        print("   - ELEVEN_API_KEY=your_elevenlabs_key")
        print("3. Restart bot: docker-compose restart")
        print("4. View logs: docker-compose logs -f youtube_farm_bot")
        print("=" * 70)

        return exit_status == 0

    except paramiko.AuthenticationException:
        print(f"\nAuthentication failed for {USERNAME}@{SERVER}")
        return False
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = deploy()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(1)
