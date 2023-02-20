from flask import request, Response, jsonify
import platform
import io, os, sys
import redis
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
# ##
# ## Configure test vs. production
# ##
redisHost = os.getenv("REDIS_HOST") or "localhost"
redisPort = os.getenv("REDIS_PORT") or 6379
redisClient = redis.StrictRedis(host=redisHost, port=redisPort, db=0)

# print("Connecting to redis({})".format(redisHost))
in_bucketname = "queue"
out_bucketname = "output"

def separate_music():
	# while(True):
	# 	print("hello world!")
	work = redisClient.blpop("toWorker")
	songHash = work[1]

	songHash = songHash.decode('utf-8')
	print("song from toWorker: ", songHash)

	try:
		minio_client.fget_object(in_bucketname, str(songHash) + ".mp3", 'input/tmp.mp3')
	except InvalidResponseError as err:
		print(err)
	

	print("retrieved song from minio !")
	# # os.chdir('../demucs')
	print("Current Dir: ", os.getcwd())

	# path = os.path.abspath('input/tmp.mp3')
	# folders = os.listdir()
	# for f in folders:
	# 	print(f)

	# result = os.path.exists("input/tmp.mp3") #giving the name of the file as a parameter.
  
	# print(result)
	os.system("python3 -m demucs.separate --out ./output tmp.mp3")


	if not minio_client.bucket_exists(out_bucketname):
		minio_client.make_bucket(out_bucketname)
	
	subtracks = os.listdir(output)
	for st in subtracks:
    		minio_client.fput_object(out_bucketname, str(st), ./output/st)

	
while(True):
	separate_music()
