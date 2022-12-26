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
        os.system(f"deploy-ocp multicluster 2  --email-ids gshanmug@redhat.com --ocp4mcoci-conf override_config.yaml --cluster1 --cluster-name odfcluster1-{suffix} --cluster-path /root/clusters/odfcluster1-{suffix} --cluster2 --cluster-name odfcluster2-{suffix} --cluster-path /root/clusters/odfcluster2-{suffix}")
    except Exception:
        pass

for i in ["10:00"]:
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
