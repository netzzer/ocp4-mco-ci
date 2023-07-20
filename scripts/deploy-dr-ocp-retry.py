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
        os.system(
            f"deploy-ocp multicluster 2  --email-ids gshanmug@redhat.com,nthomas@redhat.com,badhikar@redhat.com,anbehl@redhat.com,vbadrina@redhat.com,tjeyasin@redhat.com,amohan@redhat.com,uchapaga@redhat.com,skatiyar@redhat.com,hdavid@redhat.com,chandkum@redhat.com,dkamboj@redhat.com,dpandit@redhat.com,almartin@redhat.com,ialmeida@redhat.com --cluster1 --cluster-name drcluster1-{suffix} --cluster-path /tmp/drcluster1-{suffix} --ocp4mcoci-conf samples/2_cluster_acm_setup/override_config.yaml --cluster2 --cluster-name drcluster2-{suffix} --cluster-path /tmp/drcluster2-{suffix}  --ocp4mcoci-conf samples/2_cluster_acm_setup/override_hub_config.yaml")
    except Exception:
        pass

def jobnew(t):
    try:
        print("executing")
        suffix = get_suffix()
        os.system(
            f"deploy-ocp multicluster 2  --cluster1 --cluster-name drcluster1-{suffix} --cluster-path /tmp/drcluster1-{suffix} --ocp4mcoci-conf samples/2_cluster_acm_setup/override_config.yaml --cluster2 --cluster-name drcluster2-{suffix} --cluster-path /tmp/drcluster2-{suffix}  --ocp4mcoci-conf samples/2_cluster_acm_setup/override_hub_config.yaml")
    except Exception:
        pass

for i in ["09:40"]:
    schedule.every().monday.at(i).do(job, i)
    schedule.every().tuesday.at(i).do(job, i)
    schedule.every().wednesday.at(i).do(job, i)
    schedule.every().thursday.at(i).do(job, i)
    schedule.every().friday.at(i).do(job, i)

for i in ["09:00"]:
    schedule.every().monday.at(i).do(jobnew, i)
    schedule.every().tuesday.at(i).do(jobnew, i)
    schedule.every().wednesday.at(i).do(jobnew, i)
    schedule.every().thursday.at(i).do(jobnew, i)
    schedule.every().friday.at(i).do(jobnew, i)

while True:
    schedule.run_pending()
    time.sleep(1)