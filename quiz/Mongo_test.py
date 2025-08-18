import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
secret = os.getenv('SECRET')

myclient = pymongo.MongoClient("mongodb://localhost:32768/", username = "myTester", password = secret)
mydb = myclient["test"]
mycol = mydb["Quiz-test"]

quiz_dict = {
    "question": "What is the capital of France?",
    "options": ["Berlin", "London", "Paris", "Madrid"],
    "answer": "Paris"
}

x = mycol.insert_one(quiz_dict)
