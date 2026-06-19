"""
Simple test to verify .log file format in blob storage.
"""

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
django.setup()

from datetime import date
from auditlog.models import AuditLog
from auditlog.tasks import flush_logs_to_blob
from auditlog.blob_service import download_log_file

print("=" * 70)
print("Testing .log file format for audit logs")
print("=" * 70)

# Check current audit logs
total_logs = AuditLog.objects.count()
unflushed = AuditLog.objects.filter(flushed_to_blob=False).count()
print(f"\nTotal audit logs in DB: {total_logs}")
print(f"Unflushed logs: {unflushed}")

if unflushed > 0:
    print("\n" + "=" * 70)
    print("STEP 1: Flushing logs to blob storage as .log files")
    print("=" * 70)
    flush_logs_to_blob()
    
    # Check a sample log entry
    sample_log = AuditLog.objects.filter(flushed_to_blob=True).first()
    if sample_log and sample_log.company and sample_log.user:
        log_date = sample_log.timestamp.date()
        company_name = sample_log.company.name
        user_name = sample_log.user.name
        
        print(f"\n" + "=" * 70)
        print(f"STEP 2: Downloading .log file from blob")
        print(f"  Company: {company_name}")
        print(f"  User: {user_name}")
        print(f"  Date: {log_date}")
        print("=" * 70)
        
        log_content = download_log_file(company_name, user_name, log_date)
        
        if log_content:
            print("\n[PASS] Successfully downloaded .log file from blob")
            print("\n" + "=" * 70)
            print("STEP 3: Sample log content (first 500 chars):")
            print("=" * 70)
            print(log_content[:500])
            
            if '\n' in log_content:
                lines = log_content.strip().split('\n')
                print(f"\n[PASS] Log file contains {len(lines)} entries")
                print(f"\nSample entry format:")
                print(lines[0])
                
                if len(lines) > 1:
                    print("\nAnother entry:")
                    print(lines[1])
            else:
                print(f"\n[PASS] Log file content retrieved")
        else:
            print("\n[FAIL] Could not download log file from blob")
    else:
        print("\n[INFO] No flushed logs with company/user to test download")
else:
    print("\n[INFO] No unflushed logs available. Creating test actions...")
    print("Please run the full test script first to generate audit logs.")

print("\n" + "=" * 70)
print("Test complete!")
print("=" * 70)
