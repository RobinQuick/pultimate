@echo off
echo Starting Pultimate Dev Environment...

docker compose up -d

echo.
echo Services should be running:
echo - API: http://localhost:8000/docs
echo - Minio Console: http://localhost:9001 (minioadmin/minioadmin)
echo - Web: http://localhost:3000

echo.
echo To run tests:
echo docker compose run --rm api pytest
echo.
pause
