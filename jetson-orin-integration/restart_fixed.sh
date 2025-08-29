#!/bin/bash
pkill -f streamlit || true
sleep 2
cd /home/lionel/jetson-greenhouse
source venv/bin/activate
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
nohup streamlit run streamlit_dashboard.py --server.port 8083 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
echo "Streamlit restarted with fixed dashboard on port 8083"
sleep 3
ps aux | grep streamlit | grep -v grep
