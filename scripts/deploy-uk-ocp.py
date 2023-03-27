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
        os.system(f"deploy-ocp  --email-ids almartin@redhat.com,ialmeida@redhat.com,badhikar@redhat.com --ocp4mcoci-conf samples/deploy_ocp_cluster/override_config.yaml --cluster-name odfcluster-uk-{suffix} --cluster-path /tmp/odfcluster-uk-{suffix}")
    except Exception:
        pass

for i in ["11:30"]:
    schedule.every().monday.at(i).do(job, i)
    schedule.every().tuesday.at(i).do(job, i)
    schedule.every().wednesday.at(i).do(job, i)
    schedule.every().thursday.at(i).do(job, i)
    schedule.every().friday.at(i).do(job, i)

while True:
    schedule.run_pending()
    time.sleep(1)
