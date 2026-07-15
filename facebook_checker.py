#!/usr/bin/env python
import os
import sys
import time
import threading
import requests
import csv
from datetime import datetime
from colorama import Fore, init, Back
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import random

init(autoreset=True)

# ======================= কনফিগারেশন =======================
ACCESS_TOKEN = "EAAMaReHwwdEBR9QP4OiDi9h0gfZAbN3MRWqLxrblij4LZCYmPZCBuSgkVPZARU9pnomzeVavU8os1QNcZAQaObw8tmOZAAUjwGNYamXitsatqZAbqcASnHBgVVQml8OPUJeKWMubLfuVnJSXoDWZBF02ccCFmeWtYPLVxk2YwNgBbeAtw1Gi3VtoiZBZBtI2ZC4jW7q"  # আপনার টোকেন দিন
MAX_THREADS = 10
PROXY_FILE = "Your_Proxy.txt"

# ======================= Functions =======================

def load_proxies():
    proxies = []
    try:
        with open(PROXY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    proxies.append(line)
        if proxies:
            print(Fore.GREEN + f"✅ {len(proxies)} proxies loaded")
        return proxies
    except:
        return []

def get_proxy(proxy_list):
    if not proxy_list:
        return None
    proxy = random.choice(proxy_list)
    parts = proxy.split(':')
    if len(parts) == 4:
        server, port, user, password = parts
        proxy_url = f"http://{user}:{password}@{server}:{port}"
    elif len(parts) == 2:
        proxy_url = f"http://{proxy}"
    else:
        return None
    return {"http": proxy_url, "https": proxy_url}

def check_facebook_account(phone_number, proxy=None):
    url = f"https://graph.facebook.com/v18.0/{phone_number}"
    params = {"access_token": ACCESS_TOKEN, "fields": "id,name,email"}
    
    try:
        session = requests.Session()
        if proxy:
            session.proxies.update(proxy)
        
        response = session.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                return {
                    "status": "✅ Active",
                    "name": data.get("name", "Unknown"),
                    "id": data.get("id", ""),
                    "email": data.get("email", "N/A")
                }
        elif response.status_code == 400:
            return {"status": "❌ Not Found", "name": "N/A", "id": "", "email": "N/A"}
        else:
            return {"status": f"⚠️ Error {response.status_code}", "name": "N/A", "id": "", "email": "N/A"}
    except:
        return {"status": "⏰ Timeout/Error", "name": "N/A", "id": "", "email": "N/A"}

def save_results(results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"facebook_results_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Phone', 'Status', 'Name', 'Facebook ID', 'Email'])
        for r in results:
            writer.writerow([r['phone'], r['status'], r['name'], r['facebook_id'], r['email']])
    
    active_count = sum(1 for r in results if "Active" in r['status'])
    total = len(results)
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + f"✅ Active: {active_count}")
    print(Fore.RED + f"❌ Inactive: {total - active_count}")
    print(Fore.YELLOW + f"📁 CSV: {csv_file}")
    print(Fore.CYAN + "="*50)
    return csv_file

def load_numbers():
    filename = "/sdcard/Your_Number.txt"
    if not os.path.exists(filename):
        filename = "Your_Number.txt"
    try:
        with open(filename, "r") as f:
            numbers = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(Fore.GREEN + f"✅ {len(numbers)} numbers loaded")
        return numbers
    except FileNotFoundError:
        print(Fore.RED + f"❌ {filename} not found!")
        return []

def process_numbers(numbers, proxy_list):
    results = []
    total = len(numbers)
    lock = threading.Lock()
    
    progress_bar = tqdm(total=total, desc="Scanning", unit="num")
    
    def process_single(number):
        proxy = get_proxy(proxy_list) if proxy_list else None
        result = check_facebook_account(number, proxy)
        with lock:
            progress_bar.update(1)
            if result["status"] == "✅ Active":
                print(Fore.GREEN + f"\n✅ {number} → {result['name']}")
            else:
                print(Fore.RED + f"\n❌ {number} → {result['status']}")
        return {
            "phone": number,
            "status": result["status"],
            "name": result["name"],
            "facebook_id": result["id"],
            "email": result["email"]
        }
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(process_single, num) for num in numbers]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(Fore.RED + f"Error: {e}")
    
    progress_bar.close()
    return results

def main():
    print(Fore.CYAN + "="*50)
    print(Fore.GREEN + "🔥 Facebook Checker v3.0")
    print(Fore.CYAN + "="*50)
    
    numbers = load_numbers()
    if not numbers:
        return
    
    proxy_list = load_proxies()
    print(Fore.YELLOW + "\n🔄 Scanning...\n")
    start = time.time()
    results = process_numbers(numbers, proxy_list)
    save_results(results)
    print(Fore.MAGENTA + f"\n⏱️ Time: {time.time()-start:.2f}s")
    print(Fore.GREEN + "✅ Done!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n❌ Cancelled!")
    except Exception as e:
        print(Fore.RED + f"\n❌ Error: {e}")
