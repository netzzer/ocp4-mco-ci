import schedule
import datetime
import time
import os

nowtime = str(datetime.datetime.now())


def job(t):
    try:
        print("executing")
        os.system("cleanup-ocp --cluster-paths /root/clusters/odfcluster1 /root/clusters/odfcluster2")
    except Exception:
        pass

for i in ["21:00"]:
    schedule.every().monday.at(i).do(job, i)
    schedule.every().tuesday.at(i).do(job, i)
    schedule.every().wednesday.at(i).do(job, i)
    schedule.every().thursday.at(i).do(job, i)
    schedule.every().friday.at(i).do(job, i)
for i in ["12:00"]:
    schedule.every().sunday.at(i).do(job, i)

while True:
    schedule.run_pending()
    time.sleep(1)

