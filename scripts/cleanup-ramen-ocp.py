import schedule
import datetime
import time
import os

def get_suffix():
    nowtime = datetime.datetime.now()
    month = nowtime.strftime("%b").lower()
    day = str(nowtime.day-1)
    return month + '-' + day

def job(t):
    try:
        print("executing")
        suffix = get_suffix()
        os.system(f"cleanup-ocp  --cluster-name drcluster1-rdr-{suffix} --cluster-path /tmp/drcluster1-rdr-{suffix}")
        os.system(f"cleanup-ocp  --cluster-name drcluster2-rdr-{suffix} --cluster-path /tmp/drcluster2-rdr-{suffix}")
    except Exception:
        pass

for i in ["07:00"]:
    schedule.every().tuesday.at(i).do(job, i)
    schedule.every().wednesday.at(i).do(job, i)
    schedule.every().thursday.at(i).do(job, i)
    schedule.every().friday.at(i).do(job, i)
    schedule.every().saturday.at(i).do(job, i)

while True:
    schedule.run_pending()
    time.sleep(1)

