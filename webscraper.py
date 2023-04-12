import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin
import tkinter as tk
from tkinter import filedialog


def gui_input():
    root = tk.Tk()
    root.withdraw()

    url = input("Enter the URL to scrape: ")
    output_directory = filedialog.askdirectory(title="Choose the output directory")

    return url, output_directory


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_file(file_url, output_path, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(file_url, stream=True)
            response.raise_for_status()
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {file_url}. Attempt {attempt + 1}. Retrying...")
            time.sleep(2)
    print(f"Failed to download file: {file_url} after {retries} attempts.")


def is_internal_link(link, base_url):
    return base_url in link


def get_internal_links(soup, base_url):
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if is_internal_link(href, base_url):
            links.add(urljoin(base_url, href))
    return links


def extract_resources(soup, base_url, output_directory):
    images_directory = os.path.join(output_directory, "images")
    css_directory = os.path.join(output_directory, "css")
    js_directory = os.path.join(output_directory, "js")

    create_directory(images_directory)
    create_directory(css_directory)
    create_directory(js_directory)

    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            local_path = os.path.join(images_directory, os.path.basename(src))
            download_file(urljoin(base_url, src), local_path)
            img['src'] = os.path.basename(src)

    for css in soup.find_all('link', rel='stylesheet'):
        href = css.get('href')
        if href:
            local_path = os.path.join(css_directory, os.path.basename(href))
            download_file(urljoin(base_url, href), local_path)
            css['href'] = os.path.basename(href)

    for js in soup.find_all('script'):
        src = js.get('src')
        if src:
            local_path = os.path.join(js_directory, os.path.basename(src))
            download_file(urljoin(base_url, src), local_path)
            js['src'] = os.path.basename(src)


def bfs_scrape(base_url, output_directory):
    visited = set()
    queue = [base_url]

    while queue:
        current_url = queue.pop(0)
        if current_url not in visited:
            visited.add(current_url)

            try:
                response = requests.get(current_url)
                html_content = response.text
                soup = BeautifulSoup(html_content, "html.parser")

                extract_resources(soup, base_url, output_directory)
                internal_links = get_internal_links(soup, base_url)

                for link in internal_links:
                    if link not in visited:
                        queue.append(link)

                # Save the page to a file
                local_filename = os.path.join(output_directory, f"{len(visited)}.html")
                with open(local_filename, "w", encoding="utf-8") as file:
                    file.write(str(soup))

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {current_url}: {e}")


if __name__ == "__main__":
    url, output_directory = gui_input()
    create_directory(output_directory)
    bfs_scrape(url, output_directory)

