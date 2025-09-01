#!/bin/bash

LOGFILE="docker-helper.log"

# Create log file if it doesn't exist
if [ ! -f "$LOGFILE" ]; then
  touch "$LOGFILE"
fi


# Function to log and display output
log_and_run() {
  echo "$1" | tee -a "$LOGFILE"
  echo "$2" | tee -a "$LOGFILE"
  printf '%*s\n' "${#2}" '' | tr ' ' '-' | tee -a "$LOGFILE"
  eval "$2" 2>&1 | tee -a "$LOGFILE"
}


timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
echo "**************************************************" | tee -a "$LOGFILE"
echo "[$timestamp] Script execution started" | tee -a "$LOGFILE"
echo "**************************************************" | tee -a "$LOGFILE"
echo "Select an option:" | tee -a "$LOGFILE"
echo "1: Show Docker info" | tee -a "$LOGFILE"
echo "2: Stop all Docker processes and force delete all Docker objects" | tee -a "$LOGFILE"
echo "3: Stop all active Docker processes" | tee -a "$LOGFILE"
read -p "Enter your choice (1/2/3): " choice

case $choice in
  1)
    log_and_run "Docker version:" "docker --version"
    log_and_run "Docker Compose version:" "docker-compose --version"
    log_and_run "Running containers:" "docker ps"
    log_and_run "All containers:" "docker ps -a"
    log_and_run "Docker images:" "docker images"
    log_and_run "Docker volumes:" "docker volume ls"
    log_and_run "Docker networks:" "docker network ls"
    ;;
  2)
    log_and_run "Stopping all containers..." "docker stop \$(docker ps -aq)"
    log_and_run "Removing all containers..." "docker rm -f \$(docker ps -aq)"
    log_and_run "Removing all images..." "docker rmi -f \$(docker images -q)"
    log_and_run "Removing all volumes..." "docker volume rm -f \$(docker volume ls -q)"
    log_and_run "Removing all networks (except default ones)..." "docker network rm \$(docker network ls | grep -v 'bridge\\|host\\|none' | awk '{if(NR>1) print \$1}')"
    ;;
  3)
    log_and_run "Stopping all running containers..." "docker stop \$(docker ps -q)"
    ;;
  *)
  echo "Invalid option." | tee -a "$LOGFILE"
    ;;

esac

# Add two lines of hyphens and a blank line at the end of the log after each run
echo "--------------------------------------------------" | tee -a "$LOGFILE"
echo "--------------------------------------------------" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"