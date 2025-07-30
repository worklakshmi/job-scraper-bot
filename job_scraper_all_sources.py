
import requests
from bs4 import BeautifulSoup
import yagmail
import time
import os
from datetime import datetime
from urllib.parse import quote

CITIES = ["Hyderabad", "Chennai"]
TARGET_EXPERIENCE = 3
SEEN_JOBS_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    with open(SEEN_JOBS_FILE, 'r') as f:
        return set(line.strip() for line in f.readlines())

def save_seen_jobs(job_links):
    with open(SEEN_JOBS_FILE, 'a') as f:
        for link in job_links:
            f.write(link + '\n')

def fetch_naukri_jobs(city, seen_jobs):
    city_url = city.lower().replace(" ", "-")
    url = f"https://www.naukri.com/gcp-data-engineer-jobs-in-{city_url}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'lxml')

    job_cards = soup.find_all('article', class_='jobTuple')
    jobs = []

    for card in job_cards:
        try:
            title_tag = card.find('a', class_='title')
            title = title_tag.text.strip()
            link = title_tag['href']

            if link in seen_jobs:
                continue

            comp = card.find('a', class_='subTitle').text.strip()
            exp = card.find('li', class_='experience').text.strip()
            post_date = card.find('span', class_='footer').text.lower()

            if not any(keyword in post_date for keyword in ['1 day ago', 'today', 'few hours']):
                continue

            if str(TARGET_EXPERIENCE) not in exp:
                continue

            jobs.append({'title': title, 'company': comp, 'link': link, 'exp': exp, 'location': city})
        except:
            continue

    return jobs

def fetch_google_jobs(city, seen_jobs):
    search_query = f"site:careers.google.com GCP Data Engineer {city}"
    url = f"https://www.google.com/search?q={quote(search_query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = soup.select('a')
    jobs = []

    for tag in links:
        href = tag.get('href')
        if not href or 'careers.google.com' not in href or href in seen_jobs:
            continue
        title = tag.get_text().strip()
        jobs.append({'title': title or 'GCP Data Engineer', 'company': 'Google', 'link': href, 'exp': '3 yrs', 'location': city})
    return jobs

def fetch_linkedin_jobs(city, seen_jobs):
    search_query = f"GCP Data Engineer {city} 3 years site:linkedin.com/jobs"
    url = f"https://www.google.com/search?q={quote(search_query)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = soup.select('a')
    jobs = []

    for tag in links:
        href = tag.get('href')
        if not href or 'linkedin.com/jobs' not in href or href in seen_jobs:
            continue
        title = tag.get_text().strip()
        jobs.append({'title': title or 'GCP Data Engineer', 'company': 'LinkedIn Listing', 'link': href, 'exp': '3 yrs', 'location': city})
    return jobs

def get_all_jobs(seen_jobs):
    all_jobs = []
    for city in CITIES:
        all_jobs.extend(fetch_naukri_jobs(city, seen_jobs))
        all_jobs.extend(fetch_google_jobs(city, seen_jobs))
        all_jobs.extend(fetch_linkedin_jobs(city, seen_jobs))
    return all_jobs

def create_linkedin_message(job):
    return (
        f"Hi [Hiring Manager],\n"
        f"I came across the {job['title']} role at {job['company']} in {job['location']}. "
        "With ~3 years of experience in GCP — BigQuery, Dataflow, Airflow and Python — "
        "I’d love to connect and explore how I can support your data engineering goals.\nThanks,\n[Your Name]"
    )

def create_email_body(jobs):
    if not jobs:
        return "<p>No new jobs found today.</p>"
    body = "<h2>🚀 GCP Data Engineer Jobs – Hyderabad & Chennai (Posted Today)</h2>"
    for job in jobs:
        linkedin_msg = create_linkedin_message(job).replace('\n', '<br>')
        body += f"""
        <h3>{job['title']} @ {job['company']} – {job['location']}</h3>
        <p><strong>Experience:</strong> {job['exp']}</p>
        <p><a href="{job['link']}">Apply Now</a></p>
        <p><strong>LinkedIn Outreach:</strong><br>{linkedin_msg}</p>
        <hr>
        """
    return body

def send_email(html_body):
    yag = yagmail.SMTP(os.getenv("EMAIL"), os.getenv("APP_PASSWORD"))
    yag.send(
        to=os.getenv("EMAIL"),
        subject=f"GCP Data Engineer Jobs – {time.strftime('%b %d, %I:%M %p')}",
        contents=html_body
    )

if __name__ == "__main__":
    print("🔁 Checking for fresh jobs...")
    seen = load_seen_jobs()
    new_jobs = get_all_jobs(seen)
    print(f"📋 Total new jobs found: {len(new_jobs)}")
    send_email(create_email_body(new_jobs))
    save_seen_jobs([job['link'] for job in new_jobs])
