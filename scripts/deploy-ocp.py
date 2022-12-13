import schedule
import datetime
import time
import os

nowtime = str(datetime.datetime.now())


def job(t):
    try:
        print("executing")
        os.system("deploy-ocp multicluster 2  --email-ids gshanmug@redhat.com --ocp4mcoci-conf override_config.yaml --cluster1 --cluster-name odfcluster1 --cluster-path /root/clusters/odfcluster1 --cluster2 --cluster-name odfcluster2 --cluster-path /root/clusters/odfcluster2")
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
