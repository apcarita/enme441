#!/bin/bash
# Start development servers

echo "python backend server on port 8080..."
cd /home/adam/enme441
python3 project/main.py &
BACKEND_PID=$!

sleep 2

echo ""
echo "Starting Vite frontend dev server..."
cd /home/adam/enme441/frontend
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "====================================="
echo "Turret Control System Running"
echo "====================================="
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8080/api/*"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Servers stopped.'; exit" INT
wait

