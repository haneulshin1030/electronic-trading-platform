import subprocess
import time

# Start the server
server_process = subprocess.Popen(["python3", "server.py"])

# Wait for the server to start up
time.sleep(5)

# EXPERIMENT: # of market maker clients vs. total process duration
def experiment_mm(num_clients):
  processes = []
  for i in range(num_clients):
      p = subprocess.Popen(["python3", "market-maker-eval.py"])
      processes.append(p)

  for p in processes:
      p.communicate()

# experiment_mm(1)
# experiment_mm(2)
# experiment_mm(5)
# experiment_mm(10)
# experiment_mm(15)