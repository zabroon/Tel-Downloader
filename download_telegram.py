import sys, os, requests, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def download_telegram_post(link):
    # Convert to embedded web version if needed
    if 't.me/' in link and '/s/' not in link:
        # e.g., https://t.me/channel/123 -> https://t.me/s/channel/123
        parts = link.replace('https://t.me/', '').split('/')
        if len(parts) >= 2:
            link = f"https://t.me/s/{parts[0]}/{parts[1]}"

    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(link, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # Find message container
    msg = soup.select_one('.tgme_widget_message')
    if not msg:
        print("❌ پیام پیدا نشد. مطمئن شوید لینک عمومی است.")
        sys.exit(1)

    # Extract text
    text_div = msg.select_one('.tgme_widget_message_text')
    if text_div:
        with open('message.txt', 'w', encoding='utf-8') as f:
            f.write(text_div.get_text('\n', strip=True))
        print("✅ متن پیام در message.txt ذخیره شد.")

    # Download media
    os.makedirs('media', exist_ok=True)
    media_links = []

    # Photos
    for img in msg.select('.tgme_widget_message_photo_wrap'):
        style = img.get('style', '')
        url_match = re.search(r"url\('(.+?)'\)", style)
        if url_match:
            media_links.append(url_match.group(1))

    # Videos (thumbnail + video file)
    video_tag = msg.select_one('video')
    if video_tag:
        src = video_tag.get('src')
        if src:
            media_links.append(src)
    # Alternative: .tgme_widget_message_video
    for v in msg.select('.tgme_widget_message_video'):
        thumb_style = v.get('style', '')
        url_match = re.search(r"url\('(.+?)'\)", thumb_style)
        if url_match:
            # This is usually thumbnail, not the actual video, but we try
            media_links.append(url_match.group(1))
        # Try to find download link
        download_btn = v.select_one('.tgme_widget_message_video_btn')
        if download_btn:
            href = download_btn.get('href')
            if href:
                media_links.append(href)

    # Documents (files)
    for doc in msg.select('.tgme_widget_message_document'):
        link_tag = doc.select_one('.tgme_widget_message_document_wrap')
        if link_tag:
            href = link_tag.get('href')
            if href:
                media_links.append(href)

    for i, url in enumerate(media_links, 1):
        try:
            # Make absolute URL
            full_url = urljoin(link, url)
            filename = os.path.basename(urlparse(full_url).path) or f"media_{i}.jpg"
            filepath = os.path.join('media', filename)
            with requests.get(full_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f"📥 دانلود شد: {filename}")
        except Exception as e:
            print(f"⚠️ خطا در دانلود {url}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python download_telegram.py <t.me link>")
        sys.exit(1)
    download_telegram_post(sys.argv[1])
