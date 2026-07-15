#!/usr/bin/env python
"""
Facebook Account Checker Pro v3.0
Termux-এর জন্য তৈরি Facebook অ্যাকাউন্ট চেকার টুল
"""

import os
import sys
import time
import threading
import requests
import pandas as pd
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

# ======================= Proxy Functions =======================

def load_proxies():
    """Your_Proxy.txt ফাইল থেকে প্রোক্সি লোড করে"""
    proxies = []
    try:
        with open(PROXY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(':')
                    if len(parts) == 4:
                        server, port, username, password = parts
                        proxies.append({
                            'server': server,
                            'port': port,
                            'username': username,
                            'password': password,
                            'full': f"{server}:{port}",
                            'auth': f"{username}:{password}"
                        })
                    elif len(parts) == 2:
                        server, port = parts
                        proxies.append({
                            'server': server,
                            'port': port,
                            'username': None,
                            'password': None,
                            'full': f"{server}:{port}",
                            'auth': None
                        })
        
        if proxies:
            print(Fore.GREEN + f"✅ {len(proxies)}টি প্রোক্সি লোড হয়েছে")
            return proxies
        else:
            print(Fore.YELLOW + "⚠️ Your_Proxy.txt ফাইলটি খালি বা ফরম্যাট ভুল!")
            return []
            
    except FileNotFoundError:
        print(Fore.YELLOW + "⚠️ Your_Proxy.txt ফাইল পাওয়া যায়নি!")
        return []

def get_proxy(proxy_list):
    """প্রোক্সি লিস্ট থেকে র্যান্ডম একটি প্রোক্সি সিলেক্ট করে"""
    if not proxy_list:
        return None
    
    proxy = random.choice(proxy_list)
    
    if proxy['auth']:
        proxy_url = f"http://{proxy['auth']}@{proxy['full']}"
    else:
        proxy_url = f"http://{proxy['full']}"
    
    return {
        "http": proxy_url,
        "https": proxy_url
    }

def check_facebook_account(phone_number, proxy=None):
    """একটি ফোন নম্বর চেক করে Facebook অ্যাকাউন্ট আছে কিনা"""
    url = f"https://graph.facebook.com/v18.0/{phone_number}"
    params = {
        "access_token": ACCESS_TOKEN,
        "fields": "id,name,email"
    }
    
    try:
        session = requests.Session()
        if proxy:
            session.proxies.update(proxy)
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
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
            
    except requests.exceptions.Timeout:
        return {"status": "⏰ Timeout", "name": "N/A", "id": "", "email": "N/A"}
    except requests.exceptions.ProxyError:
        return {"status": "🔌 Proxy Error", "name": "N/A", "id": "", "email": "N/A"}
    except requests.exceptions.ConnectionError:
        return {"status": "🔌 Connection Error", "name": "N/A", "id": "", "email": "N/A"}
    except Exception as e:
        return {"status": f"❌ Error", "name": str(e)[:20], "id": "", "email": "N/A"}

def process_numbers(numbers, proxy_list):
    """মাল্টি-থ্রেডিং দিয়ে সকল নম্বর প্রসেস করে"""
    results = []
    total = len(numbers)
    completed = 0
    lock = threading.Lock()
    
    progress_bar = tqdm(total=total, desc="Scanning", unit="num", 
                        bar_format='{l_bar}%s{bar}%s{r_bar}' % (Fore.GREEN, Fore.RESET))
    
    proxy_counter = 0
    
    def process_single(number):
        nonlocal completed, proxy_counter
        
        current_proxy = None
        if proxy_list:
            proxy_counter = (proxy_counter + 1) % len(proxy_list)
            proxy = proxy_list[proxy_counter]
            current_proxy = get_proxy([proxy])
        
        result = check_facebook_account(number, current_proxy)
        
        with lock:
            completed += 1
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
        future_to_number = {executor.submit(process_single, num): num for num in numbers}
        
        for future in as_completed(future_to_number):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                number = future_to_number[future]
                results.append({
                    "phone": number,
                    "status": f"⚠️ Error",
                    "name": str(e)[:20],
                    "facebook_id": "",
                    "email": ""
                })
    
    progress_bar.close()
    return results

def save_results(results):
    """রেজাল্ট CSV এবং Excel ফাইলে সেভ করে"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    df = pd.DataFrame(results)
    
    csv_file = f"facebook_results_{timestamp}.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    excel_file = f"facebook_results_{timestamp}.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Results', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Results']
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        from openpyxl.styles import PatternFill, Font, Alignment
        header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
    
    active_count = sum(1 for r in results if "Active" in r["status"])
    total = len(results)
    
    print(Fore.CYAN + "\n" + "="*50)
    print(Fore.GREEN + f"✅ Active Accounts: {active_count}")
    print(Fore.RED + f"❌ Inactive: {total - active_count}")
    print(Fore.YELLOW + f"📁 CSV: {csv_file}")
    print(Fore.YELLOW + f"📁 Excel: {excel_file}")
    print(Fore.CYAN + "="*50)

def load_numbers():
    """Your_Number.txt থেকে নম্বর লোড করে"""
    filename = "/sdcard/Your_Number.txt"
    
    if not os.path.exists(filename):
        filename = "Your_Number.txt"
    
    try:
        with open(filename, "r") as f:
            numbers = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        if not numbers:
            print(Fore.RED + "❌ কোনো নম্বর পাওয়া যায়নি!")
            return []
        print(Fore.GREEN + f"✅ {len(numbers)}টি নম্বর লোড হয়েছে")
        return numbers
    except FileNotFoundError:
        print(Fore.RED + f"❌ {filename} ফাইল পাওয়া যায়নি!")
        return []

def main():
    print(Fore.CYAN + "="*60)
    print(Fore.GREEN + Back.BLACK + "🔥 Facebook Account Checker Pro v3.0")
    print(Fore.CYAN + "="*60)
    
    if ACCESS_TOKEN == "YOUR_FACEBOOK_ACCESS_TOKEN":
        print(Fore.RED + "❌ Facebook ACCESS_TOKEN সেট করুন!")
        return
    
    numbers = load_numbers()
    if not numbers:
        return
    
    proxy_list = load_proxies()
    
    print(Fore.YELLOW + "\n🔄 স্ক্যানিং শুরু হচ্ছে...\n")
    start_time = time.time()
    
    results = process_numbers(numbers, proxy_list)
    
    end_time = time.time()
    duration = end_time - start_time
    
    save_results(results)
    
    print(Fore.MAGENTA + f"\n⏱️ Total time: {duration:.2f} seconds")
    print(Fore.GREEN + "✅ কাজ সম্পন্ন! ধন্যবাদ 🙏")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n❌ ব্যবহারকারী বন্ধ করেছেন!")
    except Exception as e:
        print(Fore.RED + f"\n❌ Error: {str(e)}")
