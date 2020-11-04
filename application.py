from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import cv2
import numpy as np
import os
from PIL import Image
from werkzeug.utils import secure_filename
import base64
import io
from io import BytesIO
import boto3

S3_BUCKET                 = os.environ.get("elasticbeanstalk-us-east-2-491953769123")
S3_KEY                    = os.environ.get("AKIAIL6QF6SBH2LN7HFQ")
S3_SECRET                 = os.environ.get("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")

application = Flask(__name__)
# application.config.from_object("config")

s3 = boto3.client(
                "s3",
                region_name='us-east-2',
                aws_access_key_id=S3_KEY,
                aws_secret_access_key=S3_SECRET
            )

dynamodb = boto3.resource('dynamodb',
                    aws_access_key_id=S3_KEY,
                    aws_secret_access_key=S3_SECRET)

from boto3.dynamodb.conditions import Key, Attr

@application.route('/tfjs', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            number = request.form['num']
            if number == '':
                flash('CHƯA NHẬP KẾT QUẢ BỨC ẢNH')
                return render_template('tfjs.html')
                
            file = request.form['file']

            chuoi = file.split(',')

            imgdata = base64.b64decode(chuoi[-1])
            image = Image.open(io.BytesIO(imgdata))
            img = np.array(image)
            # img = cv2.resize(img,(28,28))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
            (thresh, blackAndWhiteImage) = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
            images = os.listdir(f'./static/data/{number}')
            num = len(images)
            cv2.imwrite(f'./static/data/{number}/{number}_{num + 1}.jpg',blackAndWhiteImage)

            file_name = f'static/data/{number}/{number}_{num + 1}.jpg'
            object_name = f'static/data/{number}/{number}_{num + 1}.jpg'

            region = "us-east-2"
            bucket = "elasticbeanstalk-us-east-2-491953769123"
            folder = f"static/data/{number}"
            filename = f"{number}_{num + 1}.jpg"

            s3.upload_file(file_name,bucket,object_name)  
            url = f"https://s3.console.aws.amazon.com/s3/object/{bucket}/{folder}/{filename}?region={region}"

            
            #DYNAMODB
            table = dynamodb.Table('Story')
            table.put_item(
                    Item={
            'link': url,
            'result': int(number)
                }
            )
            return redirect(url_for('submit', num=number))
        except Exception as e:
            return "Error: {}".format(e)
        
    else:
        return render_template('tfjs.html')

@application.route('/')
def hello_world():
    return render_template('index.html')

@application.route('/<num>', methods=['GET', 'POST'])
def submit(num):
    if request.method == 'POST':
        return render_template('tfjs.html')
    else:
        return render_template('submit.html')

if __name__ == "__main__":
    application.debug = True
    myPort = int(os.environ.get('PORT', 80))
    application.run(host='0.0.0.0', port=myPort, debug=True)