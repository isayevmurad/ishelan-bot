"""
boss.az Scraper — Playwright versiyası
JavaScript ilə yüklənən səhifələri oxuyur
"""

import json
import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

JOBS_FILE = "jobs.json"


def load_existing_jobs():
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)


async def scrape_boss_az_async():
    """boss.az-dan elanları çəkir (Playwright ilə)"""
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("🌐 boss.az açılır...")
        await page.goto("https://boss.az/vacancies", timeout=30000)

        # Səhifənin yüklənməsini gözlə
        await page.wait_for_load_state("networkidle", timeout=15000)
        await asyncio.sleep(2)

        # API sorğularını tut — Next.js adətən JSON API-dan data çəkir
        # Eyni zamanda HTML-dən də çəkməyə çalışırıq
        html = await page.content()

        # Elanları tap
        items = await page.query_selector_all("a[href*='/vacancies/']")

        seen_hrefs = set()
        for item in items:
            try:
                href = await item.get_attribute("href")
                if not href or href in seen_hrefs or href == "/vacancies":
                    continue
                if "/vacancies/" not in href:
                    continue
                seen_hrefs.add(href)

                text = await item.inner_text()
                text = text.strip()
                if not text or len(text) < 3:
                    continue

                # İlk sətir başlıq, ikinci sətir şirkət adı olur çox vaxt
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                title = lines[0] if lines else text
                company = lines[1] if len(lines) > 1 else ""
                salary = lines[2] if len(lines) > 2 else "Göstərilməyib"

                job_id = href.split("/")[-1].split("?")[0]

                job = {
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "salary": salary,
                    "url": "https://boss.az" + href if href.startswith("/") else href,
                    "source": "boss.az",
                    "scraped_at": datetime.now().isoformat(),
                }

                if job["title"] and len(job["title"]) > 2:
                    jobs.append(job)

            except Exception:
                continue

        await browser.close()

    # Dublikatları sil
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)

    print(f"📋 Cəmi {len(unique)} elan tapıldı")
    return unique


def scrape_boss_az():
    """Sinxron wrapper — bot.py tərəfindən çağırılır"""
    return asyncio.run(scrape_boss_az_async())


def scrape_all():
    """Yeni elanları tapır və saxlayır"""
    existing = load_existing_jobs()
    existing_ids = {j["id"] for j in existing}

    fresh = scrape_boss_az()

    new_jobs = [j for j in fresh if j["id"] not in existing_ids]

    if new_jobs:
        all_jobs = new_jobs + existing
        save_jobs(all_jobs[:500])
        print(f"✅ {len(new_jobs)} yeni elan tapıldı")
    else:
        print("ℹ️  Yeni elan yoxdur")

    return new_jobs


if __name__ == "__main__":
    jobs = scrape_all()
    for j in jobs[:5]:
        print(f"\n📌 {j['title']} — {j['company']}")
        print(f"   💰 {j['salary']}")
        print(f"   🔗 {j['url']}")
