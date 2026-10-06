#!/bin/bash
cd /opt/data/projet/nature-detective/app
pkill -f "nature-detective/app" 2>/dev/null
sleep 1
python3 server.py > server.log 2>&1 &
echo "PID $!"
sleep 4
curl -s http://localhost:8347/ -o /dev/null -w "HTTP %{http_code}\n"
