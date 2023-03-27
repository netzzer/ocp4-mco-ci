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
        os.system(f"cleanup-ocp --cluster-paths /tmp/odfcluster1-{suffix} /tmp/odfcluster2-{suffix}")
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

