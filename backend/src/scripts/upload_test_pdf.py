import httpx
import asyncio

async def upload():
    # 1. Login as admin
    client = httpx.AsyncClient(base_url="http://127.0.0.1:8000")
    login_data = {
        "username": "admin@kgpone.edu",
        "password": "admin123"
    }
    # login is urlencoded form
    res = await client.post("/api/auth/login", data=login_data)
    if res.status_code != 200:
        print("Login failed:", res.text)
        return
    print("Login successful.")
    
    # 2. Get presigned URL
    presigned_req = {
        "filename": "demo.pdf",
        "content_type": "application/pdf"
    }
    res = await client.post("/api/content/presigned-url", json=presigned_req)
    if res.status_code != 200:
        print("Presigned URL generation failed:", res.text)
        return
    
    presigned_data = res.json()
    upload_url = presigned_data["upload_url"]
    file_key = presigned_data["file_key"]
    print("Generated presigned URL:", upload_url)
    print("File key:", file_key)
    
    # 3. Upload file bytes to upload_url
    with open("c:\\Users\\munmu\\Downloads\\platinum_jubilee\\demo.pdf", "rb") as f:
        file_bytes = f.read()
    
    # We must PUT to the upload_url (direct S3 upload)
    async with httpx.AsyncClient() as upload_client:
        upload_res = await upload_client.put(upload_url, content=file_bytes, headers={"Content-Type": "application/pdf"})
        if upload_res.status_code != 200:
            print("PUT to S3 failed:", upload_res.status_code, upload_res.text)
            return
    print("File uploaded successfully to S3.")
    
    # 4. Confirm upload
    confirm_req = {
        "file_key": file_key,
        "title": "Dummy PDF Test",
        "description": "A demo PDF for testing the ingestion pipeline",
        "course_code": "CS30002",
        "academic_year": "3rd Year",
        "content_type": "application/pdf"
    }
    res = await client.post("/api/content/confirm-upload", json=confirm_req)
    if res.status_code != 201:
        print("Upload confirmation failed:", res.text)
        return
    print("Upload confirmed successfully:", res.json())

if __name__ == "__main__":
    asyncio.run(upload())
