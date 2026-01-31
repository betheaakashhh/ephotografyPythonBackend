# mongo_helper.py
import os , json
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from datetime import datetime

if os.path.exists('.env'):
    load_dotenv()

class MongoDB:
    def __init__(self):
        self.uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('MONGO_DB_NAME', 'photo-processor')
        self.client = None
        self.db = None
        
        if not self.uri:
            print("⚠️  MONGODB_URI not found in environment variables")
            # Don't raise error, allow app to start without MongoDB
            # This is important for Render to build successfully
    
    def connect(self):
        if not self.uri:
            print("❌ Cannot connect: MONGODB_URI not set")
            return False
            
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print(f"✅ Connected to MongoDB: {self.db_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
            print("📴 MongoDB connection closed")
    
    def get_collection(self, name):
        if self.db is None:  # Change this line - compare with None instead
            raise Exception("MongoDB not connected")
        return self.db[name]

    # ---- JOB OPERATIONS ----

    def insert_job(self, job_data):
     try:
        col = self.get_collection("jobs")
        job_data["created_at"] = datetime.utcnow()
        print(f"📝 Inserting job data: {json.dumps(job_data, default=str)}")  # Add this line
        result = col.insert_one(job_data)
        print(f"✅ Job inserted with ID: {result.inserted_id}")
        return str(result.inserted_id)
     except Exception as e:
        print(f"❌ Error inserting job: {e}")
        return None

    def get_job(self, job_id):
        col = self.get_collection("jobs")
        return col.find_one({"job_id": job_id}, {"_id": 0})

    def list_jobs(self, limit=100):
        col = self.get_collection("jobs")
        return list(col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))

# Singleton instance
mongo_db = MongoDB()