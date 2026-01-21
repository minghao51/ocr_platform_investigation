import asyncio
import httpx
import base64
from PIL import Image, ImageDraw
import io

async def test_full_pipeline():
    # Create test image
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), 'Invoice #12345', fill='black')
    draw.text((10, 30), 'Amount: $100.00', fill='black')
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Upload file
        print("1. Uploading test image...")
        upload_response = await client.post(
            'http://localhost:8000/api/upload',
            files={"file": ("test.png", buffer, "image/png")}
        )
        print(f"Upload status: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"Upload failed: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        file_id = upload_data.get('file_id')
        print(f"File ID: {file_id}")
        
        # Process with Nebius
        print("\n2. Processing with Nebius...")
        process_response = await client.post(
            'http://localhost:8000/api/process',
            json={
                "file_id": file_id,
                "provider": "nebius",
                "model": "Qwen/Qwen2.5-VL-72B-Instruct",
                "schema_id": None
            }
        )
        print(f"Process status: {process_response.status_code}")
        print(f"Process response: {process_response.text[:500]}")
        
        if process_response.status_code == 200:
            import json
            job_data = process_response.json()
            job_id = job_data.get('job_id')
            
            # Wait for processing to complete
            print(f"\n3. Waiting for job {job_id} to complete...")
            await asyncio.sleep(8)
            
            # Check job status
            status_response = await client.get(f'http://localhost:8000/api/jobs/{job_id}')
            print(f"Job status: {status_response.status_code}")
            
            if status_response.status_code == 200:
                job_status = status_response.json()
                print(f"Job data: {json.dumps(job_status, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
