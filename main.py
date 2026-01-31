from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse 
from rembg import remove
from services.layout_services import apply_print_layout
from services.face_crop import crop_by_face
from services.present import PRESETS
from PIL import Image
import os, uuid, time, datetime, json , asyncio
from services.mongo_helper import mongo_db 


app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB
    
    connected = mongo_db.connect()
    if not connected:
        print("Warning: Could not connect to MongoDB at startup.")

@app.on_event("shutdown")
async def shutdown_event():
    # Disconnect from MongoDB
    mongo_db.disconnect()
    

BASE_JOB_DIR = "uploads/jobs"
os.makedirs(BASE_JOB_DIR, exist_ok=True)



def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def cleanup_file(path):
    time.sleep(10)
    try:
        os.remove(path)
        print("Deleted:", path)
    except:
        pass

def create_job_folder():
    job_id = f"JOB_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    job_path = os.path.join(BASE_JOB_DIR, job_id)
    os.makedirs(job_path, exist_ok=True)
    return job_id, job_path

JOBS_LOG_FILE = "uploads/jobs_log.json"




@app.post("/remove-bg/")
async def remove_background(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    bg_color: str = Form("#ffffff"),
    preset: str = Form("passport"),
    copies: int = Form(6)
):
    try:
        job_id, job_path = create_job_folder()

        
        if mongo_db.db is None:
            print(" MongoDB not connected, attempting to reconnect...")
            mongo_db.connect()
            if mongo_db.db is None:
                print(" MongoDB still not connected")

        original_path = f"{job_path}/original.jpg"
        transparent_path = f"{job_path}/transparent.png"
        final_path = f"{job_path}/final_sheet.jpg"
        meta_path = f"{job_path}/meta.json"

        input_image = Image.open(file.file).convert("RGBA")
        input_image.convert("RGB").save(original_path, "JPEG")

        output_image = remove(input_image)
        output_image.save(transparent_path, "PNG")

        # job count
        try:
            job_count = mongo_db.get_collection("jobs").count_documents({}) + 1
        except Exception as e:
            print(f"Could not get job count: {e}")
            job_count = 1

        meta = {
            "job_id": job_id,
            "preset": preset,
            "bg_color": bg_color,
            "copies": copies,
            "created_at": datetime.datetime.now().isoformat(),
            "original_path": original_path,
            "transparent_path": transparent_path,
            "final_path": final_path,
            "status": "completed",
            "job_no": job_count,
            "price": copies * 10,
            "customer_name": "Walk-in"
        }
        
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        
        
        print(f"Attempting to save job {job_id} to MongoDB...")
        inserted_id = mongo_db.insert_job(meta)
        if inserted_id:
            print(f" Job saved to MongoDB with ID: {inserted_id}")
        else:
            print(" Failed to save job to MongoDB")

        preset_cfg = PRESETS[preset]
        bg_rgb = hex_to_rgb(bg_color)

        subject = crop_by_face(output_image, preset_cfg["face_ratio"]) if preset_cfg["face_ratio"] else output_image

        apply_print_layout(
            subject=subject,
            output_path=final_path,
            bg_color=bg_rgb,
            copies=copies,
            canvas_w=preset_cfg["canvas_w"],
            canvas_h=preset_cfg["canvas_h"],
            photo_h=preset_cfg["photo_h"],
            photo_w=preset_cfg["photo_w"]
        )

        background_tasks.add_task(cleanup_file, transparent_path)

        return FileResponse(final_path, media_type="image/jpeg", filename=f"{job_id}.jpg")
        
    except Exception as e:
        print(f"❌ Error in remove_background: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.get("/jobs")
def list_jobs():
    jobs = mongo_db.list_jobs()
    # Add download URLs to each job
    for job in jobs:
        if "job_id" in job and os.path.exists(f"uploads/jobs/{job['job_id']}/final_sheet.jpg"):
            job["download_url"] = f"http://localhost:7000/download/{job['job_id']}"
            job["preview_url"] = f"http://localhost:7000/download/{job['job_id']}"
    return jobs

@app.get("/reprint/{job_id}")
def reprint(job_id: str):
    path = f"uploads/jobs/{job_id}/final_sheet.jpg"
    if not os.path.exists(path):
        return {"error": "Job not found"}
    return FileResponse(path, media_type="image/jpeg")

@app.get("/job/{job_id}")
def job_details(job_id: str):
    job = mongo_db.get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    return job

@app.get("/download/{job_id}")
async def download_job(job_id: str):
    """Serve the final processed image for download"""
    final_path = f"uploads/jobs/{job_id}/final_sheet.jpg"
    
    if not os.path.exists(final_path):
        return {"error": "File not found"}
    
    # Return the file with download headers
    return FileResponse(
        final_path,
        media_type="image/jpeg",
        filename=f"passport_photo_{job_id}.jpg"
        
    )


@app.get("/health")
def health():
    return {"status": "ok"}


#testing endpoint
@app.get("/test-mongo")
async def test_mongo():
    try:
        # Test connection
        if mongo_db.db is None:
            return {"status": "not_connected"}
        
        # Test write operation
        test_data = {
            "test": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "Test insert"
        }
        col = mongo_db.get_collection("test_collection")
        result = col.insert_one(test_data)
        
        # Test read operation
        count = col.count_documents({})
        
        return {
            "status": "connected",
            "inserted_id": str(result.inserted_id),
            "test_count": count,
            "db_name": mongo_db.db.name
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/check-jobs")
async def check_jobs():
    try:
        if mongo_db.db is None:
            return {"status": "not_connected"}
        
        col = mongo_db.get_collection("jobs")
        jobs_count = col.count_documents({})
        recent_jobs = list(col.find().sort("created_at", -1).limit(5))
        
        # Convert ObjectId to string for JSON serialization
        for job in recent_jobs:
            if '_id' in job:
                job['_id'] = str(job['_id'])
        
        return {
            "status": "connected",
            "jobs_count": jobs_count,
            "recent_jobs": recent_jobs
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
