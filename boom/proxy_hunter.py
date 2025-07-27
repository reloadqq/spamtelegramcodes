from rich.console import Console
from rich.logging import RichHandler
import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
import os

# Set up the evil console and logging with rich
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
)
logger = logging.getLogger("evil_proxy_hunter")

# Function to validate a proxy against api.ipify.org and my.telegram.org
def validate_proxy(proxy, timeout=5):
    test_urls = [
        "https://api.ipify.org",  # General connectivity
        "https://my.telegram.org/auth/send_password"  # Telegram compatibility
    ]
    headers = {"User-Agent": UserAgent().random}
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    
    for test_url in test_urls:
        try:
            if "telegram.org" in test_url:
                response = requests.post(test_url, headers=headers, data={"phone": "+1234567890"}, proxies=proxies, timeout=timeout)
                if response.status_code not in [200, 429]:
                    return False
            else:
                response = requests.get(test_url, proxies=proxies, timeout=timeout)
                if response.status_code != 200:
                    return False
        except Exception as e:
            logger.warning(f"[bold yellow]⚠️ Proxy {proxy} failed for {test_url}: {str(e)}! ⚠️[/bold yellow]")
            return False
    
    logger.info(f"[bold green]✅ Proxy {proxy} is alive and ready for chaos! ✅[/bold green]")
    # Check for duplicates and save to proxy.txt
    try:
        with open("proxy.txt", "r") as f:
            existing_proxies = {line.strip() for line in f if line.strip()}
        if proxy in existing_proxies:
            logger.info(f"[bold yellow]🕵️‍♂️ Proxy {proxy} already in proxy.txt, skipping save! 🕵️‍♂️[/bold yellow]")
            return True
    except FileNotFoundError:
        pass
    # Save the proxy
    try:
        with open("proxy.txt", "a") as f:
            f.write(f"{proxy}\n")
            f.flush()
        logger.info(f"[bold green]😈 Proxy {proxy} saved to proxy.txt! 😈[/bold green]")
        return True
    except Exception as e:
        logger.error(f"[bold red]💥 Failed to save proxy {proxy} to proxy.txt: {e}! 💥[/bold red]")
        return True

# Function to scrape free proxies from reliable sources
def get_free_proxies():
    proxy_sources = [
        "https://free-proxy-list.net/",
        "https://www.proxy-list.download/api/v1/get?type=https",
    ]
    proxies = []
    headers = {"User-Agent": UserAgent().random}

    for source in proxy_sources:
        try:
            response = requests.get(source, headers=headers, timeout=8)
            if "proxy-list.download" in source:
                proxies.extend([line.strip() for line in response.text.splitlines() if line.strip()])
            else:
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table")
                if table:
                    rows = table.find_all("tr")[1:]
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            proxy = f"{ip}:{port}"
                            if proxy not in proxies:
                                proxies.append(proxy)
            logger.info(f"[bold red]🔥 Scraped {len(proxies)} proxies from {source}! 🔥[/bold red]")
        except Exception as e:
            logger.error(f"[bold red]💥 Failed to scrape from {source}: {e}! 💥[/bold red]")

    return proxies

# Main function to scrape and validate proxies
def main():
    console.print("[bold magenta]😈 Welcome to the Evil Proxy Hunter! 😈[/bold magenta]")
    
    # Clear proxy.txt
    try:
        if os.path.exists("proxy.txt"):
            os.remove("proxy.txt")
            logger.info("[bold yellow]🕵️‍♂️ Cleared proxy.txt for fresh chaos! 🕵️‍♂️[/bold yellow]")
        open("proxy.txt", "a").close()
        logger.info("[bold yellow]🕵️‍♂️ Created new proxy.txt! 🕵️‍♂️[/bold yellow]")
    except Exception as e:
        logger.error(f"[bold red]💥 Failed to clear/create proxy.txt: {e}! 💥[/bold red]")
        return

    proxies = get_free_proxies()
    
    if not proxies:
        console.print("[bold red]💥 No proxies found to validate! Your arsenal is empty! 💥[/bold red]")
        return

    # Validate proxies and save them immediately
    valid_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        for valid in executor.map(validate_proxy, proxies):
            if valid:
                valid_count += 1

    if valid_count == 0:
        console.print("[bold red]💥 No valid proxies found! Your arsenal is empty! 💥[/bold red]")
    else:
        console.print(f"[bold green]😈 {valid_count} live proxies saved to proxy.txt! Ready for destruction! 😈[/bold green]")

if __name__ == "__main__":
    main()