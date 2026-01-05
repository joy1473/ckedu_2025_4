from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = MongoClient(os.getenv("MONGO_DB_URL"))
    
    print("Databases found:")
    for db_name in client.list_database_names():
        print(f"\n📁 Database: {db_name}")
        db = client[db_name]
        for col_name in db.list_collection_names():
            print(f"   - {col_name} (Count: {db[col_name].count_documents({})})")

        
except Exception as e:
    print(f"Error: {e}")
