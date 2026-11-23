#!/usr/bin/env python3
"""
API Raw Data Downloader for OWN Sense Footwear Telemetry.
Handles:
1. Constructing API request to florina.ownwearable.com (supporting user_id, type_1, type_2, refresh)
2. Polling server progress with meta-refresh awareness and fast failure detection
3. Streaming download from AWS S3 directly to temporary disk file (prevents RAM exhaustion)
4. Extracting .txt telemetry files directly into input_data/
"""

import os
import re
import time
import json
import zipfile
import datetime
import html
import ssl
import tempfile
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional, Callable, Tuple

BASE_API_URL = "https://florina.ownwearable.com/pyapi/v1/rawdata/txt-zip-export/download"

# Resilient SSL Context
try:
    SSL_CONTEXT = ssl.create_default_context()
except Exception:
    SSL_CONTEXT = ssl._create_unverified_context()

def validate_user_id(user_id: Optional[str]) -> str:
    """Validates user ID format and length to prevent malformed or injection inputs."""
    if not user_id:
        return ""
    user_id = user_id.strip()
    # Normalize comma-separated IDs by trimming whitespace around each ID
    cleaned = ",".join(u.strip() for u in user_id.split(",") if u.strip())
    if not cleaned:
        return ""
    if len(cleaned) > 200:
        raise ValueError("User ID is too long (maximum 200 characters allowed).")
    if not re.match(r'^[A-Za-z0-9_,\s-]+$', cleaned):
        raise ValueError("User ID contains invalid characters. Only alphanumeric, commas, underscores, and dashes are allowed.")
    return cleaned

def validate_dates(start_date: str, end_date: str) -> None:
    try:
        d1 = datetime.date.fromisoformat(start_date)
        d2 = datetime.date.fromisoformat(end_date)
    except Exception as e:
        raise ValueError(f"Invalid date format (must be YYYY-MM-DD): {e}")

    if d2 < d1:
        raise ValueError(f"End date ({end_date}) cannot be before start date ({start_date})")

    diff_days = (d2 - d1).days
    if diff_days > 90:
        raise ValueError(f"Selected range is {diff_days} days. API allows at most 90 days.")

def extract_api_error(response_text: str) -> Optional[str]:
    """Detects explicit export failure message from HTML or JSON response (e.g. no raw data found)."""
    if not response_text:
        return None

    # Try parsing JSON response
    stripped = response_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            d = json.loads(stripped)
            if "error" in d and d["error"]:
                return str(d["error"])
            if d.get("status") in ["error", "failed"] and "message" in d:
                return str(d["message"])
        except Exception:
            pass

    unescaped = html.unescape(response_text)
    if "The export could not be prepared" in unescaped or "No raw data found" in unescaped:
        m = re.search(r'<p>[^<]*?(?:100%\s*&middot;\s*)?(No raw data found[^<]*)', unescaped, re.I)
        if m:
            return m.group(1).strip()
        m = re.search(r'<h2>([^<]+)</h2>', unescaped, re.I)
        if m:
            return m.group(1).strip()
        return "The export could not be prepared (no raw data found for the specified user and date range)."

    # Check for general alert/error banners
    m = re.search(r'<div[^>]*class=["\'][^"\']*(?:error|alert)[^"\']*["\'][^>]*>(.*?)</div>', unescaped, re.I | re.DOTALL)
    if m:
        clean = re.sub(r'<[^>]+>', ' ', m.group(1)).strip()
        if clean:
            return clean

    return None

def extract_s3_url(response_text: str) -> Optional[str]:
    """Finds presigned S3 ZIP download URL from HTML or JSON response."""
    if not response_text:
        return None

    # Try JSON response first
    stripped = response_text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            d = json.loads(stripped)
            for k in ["s3_url", "download_url", "url", "s3_download_url"]:
                if k in d and isinstance(d[k], str) and ("s3.amazonaws.com" in d[k] or ".zip" in d[k]):
                    return html.unescape(d[k].strip())
        except Exception:
            pass

    unescaped = html.unescape(response_text)

    # Check for meta refresh URL with s3
    m = re.search(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']\s*\d+\s*;\s*url=([^"\'>]+)["\']', unescaped, re.I)
    if m:
        candidate = html.unescape(m.group(1).strip())
        if "s3.amazonaws.com" in candidate or candidate.endswith(".zip") or ".zip?" in candidate:
            return candidate

    # Check for <a class="btn" href="..."> or any href with .zip or s3
    m = re.search(r'<a[^>]+href=["\']([^"\']*(?:s3\.amazonaws\.com|\.zip)[^"\']*)["\']', unescaped, re.I)
    if m:
        return html.unescape(m.group(1).strip())

    # Generic regex for S3 presigned URL
    m = re.search(r'(https://[a-zA-Z0-9.-]*s3[a-zA-Z0-9.-]*\.amazonaws\.com/[^\s"\'<>]+)', unescaped)
    if m:
        return html.unescape(m.group(1).strip())

    return None

def extract_progress_info(html_text: str) -> Tuple[int, str]:
    """
    Extracts progress percent and detailed status text (e.g. '0 of 1 user-days read · 0 files · 0 MB').
    Returns (percent, detail_message).
    """
    # If the page title indicates ready, return 100%
    m_ready = re.search(r'<title>\s*(Ready|Done|Finished)', html_text, re.I)
    if m_ready:
        return 100, "Export prepared on server"

    pct = 0
    m = re.search(r'<title>\s*(\d+)%', html_text, re.I)
    if m:
        pct = int(m.group(1))
    else:
        m = re.search(r'width:\s*(\d+)%', html_text, re.I)
        if m:
            pct = int(m.group(1))

    # Extract status details: e.g. <p>25% · 1 of 4 user-days read · 2 files · 14 MB so far
    detail = ""
    m_detail = re.search(r'<p>\s*(?:\d+%\s*&middot;\s*)?([^<]+(?:user-days|files|MB so far)[^<]*)', html_text, re.I)
    if m_detail:
        detail = m_detail.group(1).strip().replace("&middot;", "·")

    return pct, detail

def extract_meta_refresh(html_text: str) -> Tuple[Optional[int], Optional[str]]:
    """Extracts (refresh_interval_sec, next_url) from <meta http-equiv='refresh'...>."""
    m = re.search(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\']\s*(\d+)\s*(?:;\s*url=([^"\'>]+))?["\']', html_text, re.I)
    if m:
        sec = int(m.group(1))
        url = m.group(2).strip() if m.group(2) else None
        if url:
            url = html.unescape(url)
        return sec, url
    return None, None

def fetch_and_extract_rawdata(
    user_id: Optional[str] = None,
    start_date: str = "",
    end_date: str = "",
    type_1: bool = False,
    type_2: bool = False,
    output_dir: str = "input_data",
    refresh: bool = False,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    max_wait_sec: int = 600,
    poll_interval: int = 4
) -> List[str]:
    """
    Downloads raw telemetry according to the OwnWearable Raw Data Download Guide,
    streams the export ZIP to disk, extracts .txt telemetry files, and returns their paths.
    """
    start_date = start_date.strip()
    end_date = end_date.strip() if end_date else start_date

    validate_dates(start_date, end_date)

    if not type_1 and not type_2 and not user_id:
        raise ValueError("Please provide either a Worker User ID, or select All Real Users (type_1) / All Simulated Users (type_2).")

    cleaned_user_id = validate_user_id(user_id) if user_id else ""

    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    if type_1:
        params["type_1"] = "true"
    if type_2:
        params["type_2"] = "true"
    if cleaned_user_id and not (type_1 or type_2):
        params["user_id"] = cleaned_user_id

    # Construct initial request URL (includes refresh=true if requested)
    initial_params = dict(params)
    if refresh:
        initial_params["refresh"] = "true"

    query_str = urllib.parse.urlencode(params)
    base_poll_url = f"{BASE_API_URL}?{query_str}"

    initial_query = urllib.parse.urlencode(initial_params)
    next_request_url = f"{BASE_API_URL}?{initial_query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OWNSensePipeline/1.0"
    }

    target_desc = f"all real users" if type_1 else (f"all simulated users" if type_2 else f"user '{cleaned_user_id}'")
    if progress_callback:
        progress_callback({
            "phase": "connecting",
            "percent": 0,
            "message": f"Contacting API for {target_desc} ({start_date} to {end_date})..."
        })

    start_poll_time = time.time()
    s3_download_url = None

    while time.time() - start_poll_time < max_wait_sec:
        req = urllib.request.Request(next_request_url, headers=headers)
        current_sleep = poll_interval
        try:
            with urllib.request.urlopen(req, timeout=25, context=SSL_CONTEXT) as resp:
                content_type = resp.headers.get("Content-Type", "")

                # Check if response is directly a ZIP file stream
                if "application/zip" in content_type or "application/octet-stream" in content_type:
                    return _stream_and_extract_zip(resp, output_dir, progress_callback)

                # HTML page indicating progress, download link, or error
                html_body = resp.read().decode("utf-8", errors="replace")

                # 1. Fast Failure Detection: Stop immediately if export failed or no data was found!
                err_msg = extract_api_error(html_body)
                if err_msg:
                    raise RuntimeError(f"Cloud API: {err_msg}")

                # 2. Check if presigned S3 download link is ready
                s3_url = extract_s3_url(html_body)
                if s3_url:
                    s3_download_url = s3_url
                    if progress_callback:
                        progress_callback({
                            "phase": "ready",
                            "percent": 100,
                            "message": "Export prepared on server! Starting S3 download..."
                        })
                    break

                # 3. Parse progress percent and status details
                pct, detail = extract_progress_info(html_body)
                elapsed = int(time.time() - start_poll_time)
                msg = f"Server preparing ZIP export ({pct}% complete, {elapsed}s elapsed)"
                if detail:
                    msg += f" - {detail}"
                else:
                    msg += "..."

                if progress_callback:
                    progress_callback({
                        "phase": "preparing",
                        "percent": pct,
                        "message": msg
                    })

                # 4. Extract next polling URL and server refresh interval
                meta_sec, meta_url = extract_meta_refresh(html_body)
                if meta_sec:
                    current_sleep = max(2, min(10, meta_sec))
                if meta_url:
                    # Strip &refresh=true from subsequent polls so server is not reset
                    if "refresh=true" in meta_url:
                        meta_url = re.sub(r'[?&]refresh=true', '', meta_url)
                        if "?" not in meta_url and "&" in meta_url:
                            meta_url = meta_url.replace("&", "?", 1)
                    next_request_url = meta_url
                else:
                    next_request_url = base_poll_url

        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="replace") if he.fp else ""
            clean_err = extract_api_error(err_body) or f"HTTP {he.code}: {he.reason}"
            raise RuntimeError(f"API request failed ({clean_err})")
        except RuntimeError:
            raise
        except Exception as e:
            if progress_callback:
                progress_callback({
                    "phase": "retrying",
                    "percent": 0,
                    "message": f"Waiting for API response ({e}). Retrying in {poll_interval}s..."
                })
            next_request_url = base_poll_url
            current_sleep = poll_interval

        time.sleep(current_sleep)

    if not s3_download_url:
        raise TimeoutError(f"Export did not complete within {max_wait_sec} seconds.")

    # Stream the ZIP file from presigned AWS S3 link directly to disk
    if progress_callback:
        progress_callback({
            "phase": "downloading",
            "percent": 0,
            "message": "Downloading raw telemetry ZIP file from AWS S3..."
        })

    s3_req = urllib.request.Request(s3_download_url, headers=headers)
    with urllib.request.urlopen(s3_req, timeout=90, context=SSL_CONTEXT) as s3_resp:
        return _stream_and_extract_zip(s3_resp, output_dir, progress_callback)


MAX_FILE_BYTES = 250 * 1024 * 1024    # 250 MB per file limit
MAX_TOTAL_BYTES = 4096 * 1024 * 1024  # 4 GB total uncompressed limit

def _stream_and_extract_zip(
    resp,
    output_dir: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> List[str]:
    """Streams ZIP content directly to a temporary file on disk and extracts safely."""
    total_len = resp.headers.get("Content-Length")
    total_bytes = int(total_len) if total_len and total_len.isdigit() else 0

    downloaded = 0
    chunk_size = 512 * 1024 # 512 KB chunks

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
        tmp_path = tmp_zip.name
        try:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                tmp_zip.write(chunk)
                downloaded += len(chunk)
                if total_bytes > 0:
                    pct = min(100, int((downloaded / total_bytes) * 100))
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total_bytes / (1024 * 1024)
                    if progress_callback:
                        progress_callback({
                            "phase": "downloading",
                            "percent": pct,
                            "message": f"Downloading ZIP: {mb_down:.1f} MB / {mb_total:.1f} MB ({pct}%)..."
                        })

            tmp_zip.flush()
            return _extract_zip_file(tmp_path, output_dir, progress_callback)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

def _extract_zip_file(
    zip_path: str,
    output_dir: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> List[str]:
    """Extracts raw telemetry files from a zip file on disk into output_dir with security bounds."""
    if progress_callback:
        progress_callback({
            "phase": "extracting",
            "percent": 100,
            "message": "Unpacking telemetry files into input_data/..."
        })

    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    extracted_files = []
    total_uncompressed = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Skip directories or macOS metadata
            if member.is_dir() or "__MACOSX" in member.filename:
                continue

            # Zip bomb mitigation
            if member.file_size > MAX_FILE_BYTES:
                raise ValueError(f"Zip member '{member.filename}' exceeds {MAX_FILE_BYTES // (1024*1024)}MB limit.")
            total_uncompressed += member.file_size
            if total_uncompressed > MAX_TOTAL_BYTES:
                raise ValueError(f"Total uncompressed zip content exceeds {MAX_TOTAL_BYTES // (1024*1024)}MB safety threshold.")

            fname = os.path.basename(member.filename)
            # Enforce clean filename pattern
            if not re.match(r'^[A-Za-z0-9_.\s-]+$', fname):
                continue

            # We care about .txt and .jsonl files
            if not (fname.endswith(".txt") or fname.endswith(".jsonl")):
                continue

            dest_path = os.path.abspath(os.path.join(abs_output_dir, fname))
            # Zip slip mitigation: ensure target path is within abs_output_dir
            if os.path.commonpath([abs_output_dir, dest_path]) != abs_output_dir:
                raise ValueError(f"Path traversal detected in zip archive for member: {fname}")

            with zf.open(member) as src_f, open(dest_path, "wb") as dst_f:
                while True:
                    buf = src_f.read(512 * 1024)
                    if not buf:
                        break
                    dst_f.write(buf)

            extracted_files.append(dest_path)

    if progress_callback:
        progress_callback({
            "phase": "extracted",
            "percent": 100,
            "message": f"Successfully extracted {len(extracted_files)} telemetry file(s) into '{output_dir}'!"
        })

    return extracted_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download raw telemetry data from OwnWearable Cloud API")
    parser.add_argument("--user", help="Worker / User ID (e.g. 3mSa_i or comma-separated list)")
    parser.add_argument("--start", required=True, help="Start Date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End Date (YYYY-MM-DD, defaults to start date)")
    parser.add_argument("--type-1", action="store_true", help="Download all real users")
    parser.add_argument("--type-2", action="store_true", help="Download all simulated users")
    parser.add_argument("--out", default="input_data", help="Output directory (default: input_data)")
    parser.add_argument("--refresh", action="store_true", help="Force fresh export rebuild on server")
    args = parser.parse_args()

    end_date = args.end if args.end else args.start

    target = "All real users" if args.type_1 else ("All simulated users" if args.type_2 else f"User '{args.user}'")
    print(f"[*] Downloading telemetry for {target} from {args.start} to {end_date}...")
    try:
        files = fetch_and_extract_rawdata(
            user_id=args.user,
            start_date=args.start,
            end_date=end_date,
            type_1=args.type_1,
            type_2=args.type_2,
            output_dir=args.out,
            refresh=args.refresh,
            progress_callback=lambda p: print(f"[{p.get('percent', 0):>3}%] {p.get('message', '')}")
        )
        print(f"\n[+] Successfully saved {len(files)} file(s):")
        for f in files:
            print(f"    - {f}")
    except Exception as err:
        print(f"\n[!] Error: {err}")
        exit(1)
