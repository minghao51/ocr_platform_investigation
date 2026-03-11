# Troubleshooting

## Login Fails

Check:

- the user exists in the database
- the password is correct
- `JWT_SECRET_KEY` is set consistently for the running backend

Useful command:

```bash
cd backend
uv run python -m backend.cli list-users
```

## Upload Returns 401 or 403

Uploads require authentication. Log in through the UI first, or include a bearer token if you are calling the API directly.

## Upload Fails Because of File Type

Current upload route accepts:

- `.jpg`
- `.jpeg`
- `.png`
- `.pdf`

If you need another format, convert it before upload or extend [backend/routers/upload.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/upload.py).

## Upload Fails Because of File Size

The default limit is 10 MB.

Relevant settings:

- `.env`: `MAX_FILE_SIZE`
- code: [backend/routers/upload.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/upload.py)

## No Providers or Models Show Up

Usually means no valid API keys are configured.

Check:

- `.env`
- provider-specific key names
- backend restart after editing environment variables

## Processing Fails Immediately

Check:

- the uploaded file still exists in `data/uploads`
- the selected schema is valid
- the selected provider has a configured API key
- your prompt/options are not malformed

## Job Stays in Pending or Processing

Check backend logs first. Common causes:

- provider API timeout
- malformed schema causing downstream failure
- missing external credentials

If the UI loses the live connection, the job may still complete. Refresh History and inspect the job there.

## Text Extraction Complains About File Type

The dedicated text route only supports PDFs. Use the main smart extraction flow for images and scans.

## Frontend Loads but API Calls Fail

Check:

- backend is running on `http://localhost:8000`
- `CORS_ORIGINS` includes your frontend origin
- the frontend is not pointing at a stale backend session

## Reset Local State

If your local setup is messy:

1. Stop the app.
2. Remove the local SQLite file if you want a clean database.
3. Restart the backend and recreate users as needed.

Example:

```bash
rm -f data/ocr_platform.db
```

Be careful: that deletes local app data.
