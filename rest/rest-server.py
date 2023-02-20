##
from flask import Flask, request, Response, jsonify
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
from minio import Minio
from minio.error import InvalidResponseError
import os
import base64
import random
import jsonpickle
import json

minioHost = os.getenv("MINIO_HOST") or "localhost:9000"
minioUser = os.getenv("MINIO_USER") or "rootuser"
minioPasswd = os.getenv("MINIO_PASSWD") or "rootpass123"

minio_client = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)
##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

print("Connecting to redis({})".format(redisHost))

bucketname = "queue"
app = Flask(__name__)

##
## Your code goes here..
##
@app.route('/apiv1/separate', methods=['POST'])
def separate():
  # import pdb;pdb.set_trace()
  r = request 
  data = json.loads(r.data)
  mp3_encoded = data['mp3']

  #decode encoded data
  with open("tmp.mp3", "wb") as f:
    f.write(base64.b64decode(mp3_encoded))

  if not minio_client.bucket_exists(bucketname):
    minio_client.make_bucket(bucketname)
  
  hash = random.getrandbits(128)
  minio_client.fput_object(bucketname, str(hash)+".mp3", './tmp.mp3')

  redisClient.lpush("toWorker",str(hash))
    
  # print("----- DEBUG ----- hash: ",hash)
  # print("----- DEBUG ----- reason: ", "Song enqueued for separation")
  
  response = {'hash': hash, "reason": "Song enqueued for separation" }
  # print("----- DEBUG ----- Response: ", response)
  
  response_pickled = jsonpickle.encode(response)
    
  #delete file
  os.remove("tmp.mp3")
  return Response(response=response_pickled, status=200, mimetype="application/json")
    

@app.route('/apiv1/queue/', methods=['GET'])
def queue_dump():

  queue_contents = redisClient.lrange("toWorker", 0, -1)[0].decode()
  # for q in queue_contents:
  #   queue_contents = q['py/b64']


  response = {"queue": queue_contents}
  response_pickled = jsonpickle.encode(response)
  return Response(response=response_pickled, status=200, mimetype="application/json")

@app.route('apiv1/track/<string:track>/<string:subtrack>', methods=['GET'])
def track(track, subtrack):
  
  redisClient.lpush("logging", str({rest.logs.track":"new request received"}))
  try:
      data = client.get_object(out_bucket, f"{track}/{subtrack}.mp3)
      with open(f"{track}.mp3", 'wb') as file_data:
        for dstr in data.stream(32*1024):
            file_data.write(dstr)
        redisClient.lpush("logging", str({rest.logs.track":f"mp3_downloaded - {track}/{subtrack}.mp3))
      return (f'{track}/{subtrack} file downloaded')
  except Exception as e:
      redisClient.lpush("logging", "Error in rest.logs.track")
      return {"Error": {str(e)} }                                       
    
@app.route('apiv1/remove/<string:track>', methods=['GET'])
def remove_track(track):
  try:
    minio_client.remove_object("queue", f"{track}.mp3")
    return (f'{track}.mp3 deleted successfully)
  except Exception as e:
    return {"Error": {str(e)}}
    
app.run('0.0.0.0',5959)
