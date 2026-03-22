#!/usr/bin/env python3
"""
money4band / Bandwidth Stack Setup
Installs Docker + runs EarnApp, Honeygain, IPRoyal, PacketStream,
Repocket, Peer2Profit, Traffmonetizer as containers.
Earn $60-150/month passively from idle bandwidth.
"""
import subprocess, sys, os, platform

DOCKER_COMPOSE = """version: '3.8'
services:
  earnapp:
    image: fazalfarhan01/earnapp:lite
    restart: always
    environment:
      - EARNAPP_UUID=sdk-node-nysr-proflow-01
    volumes:
      - earnapp_data:/etc/earnapp

  honeygain:
    image: honeygain/honeygain:latest
    restart: always
    command: -tou-accept -email nyspotlightreport@gmail.com -pass REPLACE_HONEYGAIN_PASS -device NYSR-PC-01

  iproyal:
    image: iproyal/pawns-cli:latest
    restart: always
    command: -accept-tos -email=nyspotlightreport@gmail.com -password=REPLACE_IPROYAL_PASS -device-name=NYSR-PC -device-id=nysr-01

  packetstream:
    image: packetstream/psclient:latest
    restart: always
    environment:
      - CID=REPLACE_PACKETSTREAM_CID

  repocket:
    image: repocket/repocket:latest
    restart: always
    environment:
      - RP_EMAIL=nyspotlightreport@gmail.com
      - RP_API_KEY=REPLACE_REPOCKET_KEY
"""

def check_docker():
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    return False

def install_docker_windows():
    print("Docker not found. Downloading Docker Desktop...")
    url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    subprocess.run(["powershell", "-Command", f"Start-Process '{url}'"])
    print("Install Docker Desktop, restart your PC, then run this script again.")
    input("Press ENTER to open Docker download page...")
    os.startfile("https://www.docker.com/products/docker-desktop/")

def run():
    print("=" * 50)
    print("  money4band Bandwidth Stack Setup")
    print("  Earn $60-150/month from idle bandwidth")
    print("=" * 50)
    print()
    
    if not check_docker():
        if platform.system() == "Windows":
            install_docker_windows()
        else:
            print("Install Docker: https://docs.docker.com/get-docker/")
        return
    
    # Save compose file
    with open("docker-compose.passive.yml", "w") as f:
        f.write(DOCKER_COMPOSE)
    
    print("docker-compose.passive.yml saved.")
    print()
    print("BEFORE RUNNING - update passwords in docker-compose.passive.yml:")
    print("  - REPLACE_HONEYGAIN_PASS -> your Honeygain password")
    print("  - REPLACE_IPROYAL_PASS -> your IPRoyal password (iproyal.com)")
    print("  - REPLACE_PACKETSTREAM_CID -> your PacketStream CID (packetstream.io)")
    print("  - REPLACE_REPOCKET_KEY -> your Repocket API key (repocket.co)")
    print()
    
    go = input("Have you updated the passwords? (y/n): ").strip().lower()
    if go == "y":
        print("Starting bandwidth stack...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.passive.yml", "up", "-d"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("Bandwidth stack RUNNING!")
            print("Earnings start within 24 hours.")
            print("Monitor at: dashboard.honeygain.com | earnapp.com/dashboard")
        else:
            print(f"Error: {result.stderr[:200]}")
    else:
        print("Update the passwords then run again.")

if __name__ == "__main__":
    run()
