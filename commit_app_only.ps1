# Run this script in PowerShell from D:\Arogya to commit only necessary app files.
# Close Cursor/IDE or any Git GUI before running to avoid index.lock issues.

Set-Location "D:\Arogya"

# Remove stale lock
if (Test-Path ".git\index.lock") { Remove-Item -Force ".git\index.lock" }

# Stage only app files (root .gitignore already excludes ffmpeg, .rar, .env)
git add .gitignore
git add AIStudyCoach/

# Optional: exclude database from commit (uncomment next 2 lines to skip arogya_mitra.db)
# (Get-Content AIStudyCoach\.gitignore) -replace '!arogya_mitra.db','# !arogya_mitra.db' | Set-Content AIStudyCoach\.gitignore
# git add AIStudyCoach/.gitignore

git status --short

# Commit
git commit -m "Add Arogya Mitra app: AIStudyCoach source, config, and docs only"

Write-Host "Done. Push with: git push origin main"
