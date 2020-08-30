#these imports for normal operations
import cv2
import numpy as np
import datetime

#ObjectStorage
import ibm_boto3
from ibm_botocore.client import Config, ClientError

#CloudantDB
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import requests

#for ibm iot platform
import time
import sys
import ibmiotf.application
import ibmiotf.device
import random

# importing web browser to prepare for simulation
import webbrowser

#visual recognition
import json
from watson_developer_cloud import VisualRecognitionV3

visual_recognition = VisualRecognitionV3(
    '2018-03-19',
    iam_apikey='KL11qNCtdmrm3mpty13OfABOvu2IVCIMHl2xV06fnFCm')

#Provide your IBM Watson Device Credentials
organization = "61f75s"
deviceType = "raspberrypi"
deviceId = "123456"
authMethod = "token"
authToken = "1234567890"

# Initialize GPIO
def myCommandCallback(cmd):
        print("Command received: %s" % cmd.data)
        #print(type(cmd.data))
        i=cmd.data['cmd']
        if i=='alert':
                print("alerting through message")
                r = requests.get('https://www.fast2sms.com/dev/bulk?authorization=0K73zE2MYSWGcOmb5L8kd6CQxP4jeIJgAvqy1XhoiuU9ZnBNtDmfJbIF73nah5ld6kKWjHgBOViPR1zZ&sender_id=FSTSMS&message=Some one is at door,carefully check&language=english&route=p&numbers=8105114611')
                print(r.status_code)
                print("******* Alert message sent to relatives Successfully *******")
        
                

#credentials usage and connecting to the ibmiot device
try:
        deviceOptions = {"org": organization, "type": deviceType, "id": deviceId, "auth-method": authMethod, "auth-token": authToken}
        deviceCli = ibmiotf.device.Client(deviceOptions)#.............................................

#When ibmiot device don't connect,exception wil be caught
except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()

# Connect and send a datapoint "hello" with value "world" into the cloud as an event of type "greeting" 10 times
deviceCli.connect()

#haarcascade classifiers for the classification
face_classifier=cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
eye_classifier=cv2.CascadeClassifier("haarcascade_eye.xml")


# Constants for IBM COS values
COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
COS_API_KEY_ID = "px2YsRxX3GVSL25sZLnNIisVYqQAouLG5ABY8F7NQBrq" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
COS_RESOURCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/8afdebb604314712854f720076b9cd1d:422e18ca-30b6-440f-b6c6-79cf78342e1f::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"
COS_AUTH_ENDPOINT = "https://iam.cloud.ibm.com/identity/token"

# Create resource
cos = ibm_boto3.resource("s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_RESOURCE_CRN,
    ibm_auth_endpoint=COS_AUTH_ENDPOINT,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT
)


#Provide CloudantDB credentials such as username,password and url
#b83321b7-0675-4ce1-8ebf-acc367bd5d06-bluemix
client = Cloudant("b83321b7-0675-4ce1-8ebf-acc367bd5d06-bluemix", "2b5d8a8d289564ffece76a6ccc9c0462ba8622a7f859bd4f9d86d7d4006b65cc", url="https://b83321b7-0675-4ce1-8ebf-acc367bd5d06-bluemix:2b5d8a8d289564ffece76a6ccc9c0462ba8622a7f859bd4f9d86d7d4006b65cc@b83321b7-0675-4ce1-8ebf-acc367bd5d06-bluemix.cloudantnosqldb.appdomain.cloud")
client.connect()

#Provide your database name

database_name = "sample"

my_database = client.create_database(database_name)

if my_database.exists():
   print(f"'{database_name}' successfully created.")



def multi_part_upload(bucket_name, item_name, file_path):
    try:
        print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
        # set 5 MB chunks
        part_size = 1024 * 1024 * 5

        # set threadhold to 15 MB
        file_threshold = 1024 * 1024 * 15

        # set the transfer threshold and chunk size
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # the upload_fileobj method will automatically execute a multi-part upload
        # in 5 MB chunks for all files over 15 MB
        with open(file_path, "rb") as file_data:
            cos.Object(bucket_name, item_name).upload_fileobj(
                Fileobj=file_data,
                Config=transfer_config
            )

        print("Transfer for {0} Complete!\n".format(item_name))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to complete multi-part upload: {0}".format(e))


#It will read the first frame/image of the video
video=cv2.VideoCapture(0)
calling=0
while True:
    
    print("Calling this for: "+str(calling)+"  time")
    #capture the first frame
    check,frame=video.read()
    gray=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    

    #detect the faces from the video using detectMultiScale function
    faces=face_classifier.detectMultiScale(gray,1.3,5)
    eyes=eye_classifier.detectMultiScale(gray,1.3,5)

    print(faces)
    
    #drawing rectangle boundries for the detected face
    for(x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (127,0,255), 2)
        cv2.imshow('Face detection', frame)
        picname=datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
        imkage = picname+".jpg"
        cv2.imwrite(imkage,frame)
        multi_part_upload("securitys1", picname+".jpg", picname+".jpg")
        json_document={"link":COS_ENDPOINT+"/"+"securitys1"+"/"+picname+".jpg"}
        new_document = my_database.create_document(json_document)
        # Check that the document exists in the database.
        if new_document.exists():
            print(f"Document successfully created.")
        # r = requests.get('https://www.fast2sms.com/dev/bulk?authorization=xfCqPY5rnfgh3RaUAjtPhZovgo2mVhwBEeVOgFKJm7cpp8gbh1aA0KGIIsah&sender_id=FSTSMS&message=This is test message&language=english&route=p&numbers=8105114611')
        #`print(r.status_code)


        
    #drawing rectangle boundries for the detected eyes
    for(ex,ey,ew,eh) in eyes:
        cv2.rectangle(frame, (ex,ey), (ex+ew,ey+eh), (127,0,255), 2)
        cv2.imshow('Face detection', frame)
        
    time.sleep(2)
    deviceCli.commandCallback = myCommandCallback
    
    print("*********Sending data to visual recognition trained part,to have test result*********")
    with open('./'+imkage, 'rb') as images_file:
        classes = visual_recognition.classify(
            images_file,
            threshold='0.85',
	    classifier_ids='DefaultCustomModel_1536764358').get_result()
    c=json.dumps(classes, indent=2)
    c=json.loads(c)
    c=len(c['images'][0]['classifiers'][0]['classes'])
    time.sleep(10)
    print("Sleep over")
    print(c)
    if c > 0:
            print("opening door ")
            time.sleep(2)
            webbrowser.open("https://www.tinkercad.com/things/7EkC2ub7QzI-micro-servo/editel")
        
    #waitKey(1)- for every 1 millisecond new frame will be captured
    Key=cv2.waitKey(10000)
    if Key==ord('q'):
        #release the camera
        video.release()
        #destroy all windows
        cv2.destroyAllWindows()
        break

