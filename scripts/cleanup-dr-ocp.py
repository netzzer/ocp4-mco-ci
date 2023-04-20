import schedule
import datetime
import time
import os

def get_suffix():
    nowtime = datetime.datetime.now()
    month = nowtime.strftime("%b").lower()
    day = str(nowtime.day)
    return month + '-' + day

def job(t):
    try:
        print("executing")
        suffix = get_suffix()
        os.system(f"cleanup-ocp  --cluster-name drcluster1-{suffix} --cluster-path /tmp/drcluster1-{suffix}")
        os.system(f"cleanup-ocp  --cluster-name drcluster2-{suffix} --cluster-path /tmp/drcluster2-{suffix}")
    except Exception:
        pass

for i in ["21:00"]:
    schedule.every().monday.at(i).do(job, i)
    schedule.every().tuesday.at(i).do(job, i)
    schedule.every().wednesday.at(i).do(job, i)
    schedule.every().thursday.at(i).do(job, i)
    schedule.every().friday.at(i).do(job, i)

while True:
    schedule.run_pending()
    time.sleep(1)

