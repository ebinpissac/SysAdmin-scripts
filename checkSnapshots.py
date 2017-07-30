#Ebin Issac - June 2017
#!/usr/bin/python
import boto
import boto3
import os
import sys
from boto import ec2
import datetime
from datetime import timedelta
import boto.sns


def checkSnapshot():
    # connect to aws
    connection = boto.ec2.connect_to_region("ap-southeast-1",
                                            aws_access_key_id=access_key,
                                            aws_secret_access_key=secret_key)
    # get all instances
    ec2list = connection.get_all_instances()
    for reservation in ec2list:
        # finding the name from instance id
        for i in reservation.instances:
            if 'Name' in i.tags:
                instance_name = i.tags['Name']
            else:
                instance_name = ""
            # getting all volumes in that instance
            volumes = connection.get_all_volumes(filters={'attachment.instance-id': i.id})

            for volume in volumes:
                #variable to check if there is any snapshot created today for this volume
                todaysSnapshots=0
                dbSnapshots=0
                daySnapshots=0
                weekSnapshots=0
                monthSnapshots=0
                yearSnapshots=0
                otherSnapshots=0
                # getting all snapshots for the selected volume
                snapshots = connection.get_all_snapshots(filters={'volume-id': volume.id})
                # count total snapshots with day/month/year tags
                if len(snapshots) != 0:
                    for snaps in snapshots:
                        if str("day_snapshot")  in str(snaps.description):
                            daySnapshots=daySnapshots+1
                        elif str("week_snapshot")  in str(snaps.description):
                            weekSnapshots=weekSnapshots+1
                        elif str("month_snapshot") in str(snaps.description):
                            monthSnapshots=monthSnapshots+1
                        elif str("year_snapshot")  in str(snaps.description):
                            yearSnapshots=yearSnapshots+1
                        elif str("DB_01")  in str(snaps.description):
                            dbSnapshots=dbSnapshots+1
                        else:
                            otherSnapshots=otherSnapshots+1

                    for snaps in snapshots:
                        # checking the snapshot date, if it is yesterday's date, then write to success file
                        # yesterday is used because snaps.start_time gives the time in GMT. Our snapshots are run at 3 am which is around 7 pm the previous day
                        startTimeInSGT = (
                        datetime.datetime.strptime(snaps.start_time, '%Y-%m-%dT%H:%M:%S.%fZ') + timedelta(hours=8))
                        if str(today) in str(startTimeInSGT):
                            #increment the counter if any snapshot created today
                            todaysSnapshots = todaysSnapshots+1
                            successFile.write(instance_name)
                            successFile.write(",")
                            successFile.write(i.id)
                            successFile.write(",")
                            successFile.write(snaps.volume_id)
                            successFile.write(",")
                            successFile.write(snaps.id)
                            successFile.write(",")
                            successFile.write(snaps.description)
                            successFile.write(",")
                            successFile.write(snaps.progress)
                            successFile.write(",")
                            successFile.write(snaps.status)
                            successFile.write(",")
                            successFile.write(str(snaps.encrypted))
                            successFile.write(",")
                            successFile.write(str(snaps.volume_size))
                            successFile.write(",")
                            #convert the time to SGT
                            #startTimeInSGT=(datetime.datetime.strptime(snaps.start_time, '%Y-%m-%dT%H:%M:%S.%fZ')+timedelta(hours=8))
                            successFile.write(str(startTimeInSGT) )
                            successFile.write(",")
                            successFile.write(str(daySnapshots))
                            successFile.write(",")
                            successFile.write(str(weekSnapshots))
                            successFile.write(",")
                            successFile.write(str(monthSnapshots))
                            successFile.write(",")
                            successFile.write(str(yearSnapshots))
                            successFile.write(",")
                            successFile.write(str(dbSnapshots))
                            successFile.write(",")
                            successFile.write(str(otherSnapshots) + "\n")

                # if no snapshot found today, wruite to error file
                if todaysSnapshots==0:
                    '''print "No snapshot created on " + today + " for volume id " + str(
                        volume) + " of instance " + str(instance_name)'''
                    errorFile.write(instance_name)
                    errorFile.write(",")
                    errorFile.write(i.id)
                    errorFile.write(",")
                    errorFile.write(str(volume) + "\n")

    errorFile.close()
    successFile.close()
def uploadToS3():
    #connect to S3
    s3 = boto3.resource("s3",
                        aws_access_key_id=corp_access_key,
                        aws_secret_access_key=corp_secret_key)
    #upload to S3
    s3.meta.client.upload_file(errorFileName, 'managed-customers-snapshot-reports', folderToUpload.format(errorFileName))
    s3.meta.client.upload_file(successFileName, 'managed-customers-snapshot-reports', folderToUpload.format(successFileName))
def deleteLocalFiles():
    #deleting local files
    os.remove(successFileName)
    os.remove(errorFileName)
def sendEmailSNS():
    #connect to SNS
    snsConnection=boto.sns.connect_to_region("ap-southeast-1",
                                             aws_access_key_id=corp_access_key,
                                             aws_secret_access_key=corp_secret_key)
    topicarn = "YOUR SNS TOPIC ARN"
    message = "SOME MESSAGE"
    message_subject = env+" Daily snapshot report for " + today
    #publish to stopic
    publication = snsConnection.publish(topicarn, message, subject=message_subject)

    print publication



#Params :
'''
    1- access key to the env
    2- secret key to the env
    3- env name : this is to add to the output file and to upload to S3
    4- access key to the corp env
    5- secret key to the corp env.
'''
if len(sys.argv) != 6:
    print len(sys.argv)
    print "Please give necessary args"
    exit (0)

#defining global variables
today= datetime.datetime.today().strftime('%Y-%m-%d')                       #today's date
yesterday = (datetime.datetime.today()-timedelta(1)).strftime('%Y-%m-%d')   #yesterday's date
access_key=sys.argv[1]                                                      #access key to the env
secret_key=sys.argv[2]                                                      #secret key to the env
env=sys.argv[3]                                                             #environment- this can be IT198-Prod, IT198-API, IT198-Stg
corp_access_key=sys.argv[4]                                                 #access key to 1CS managed Svc account
corp_secret_key=sys.argv[5]                                                 #secret key to 1Cs managed Svc account
successFileName=today+"_"+env+".csv"                                        #file name to save the successful snapshots
errorFileName=today+"_"+env+"_noSnapshots.csv"                                    #file name to save vols with no snapshots
folderToUpload=env+"/{}"                                                    #folder name in the S3 bucket to upload. This will be same as the env

#opening the files and write the headings
successFile = open('%s' % successFileName, 'w')
successFile.write("Instance name, Instance ID, Volume ID,Snapshot ID, Description, Progress, Status, Encrypted, Volume Size(GB), Start Time, Day Snapshots, Week snapshots, Month snapshots, Year Snapshots, DB Snapshots, Other Snapshots\n")
errorFile = open('%s' % errorFileName, 'w')
errorFile.write("Instance name, Instance ID, Volume ID\n")


#calling the functions
checkSnapshot()
uploadToS3()
sendEmailSNS()
deleteLocalFiles()