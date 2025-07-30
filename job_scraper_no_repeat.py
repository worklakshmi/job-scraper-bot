import requests
from bs4 import BeautifulSoup
import yagmail
import time
import os

CITIES = ["Hyderabad", "Chennai"]
TARGET_EXPERIENCE = 3
SEEN_JOBS_FILE = "seen_jobs.txt"

# Load already sent job URLs
def load_seen_jobs():
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()
    with open(SEEN_JOBS_FILE, 'r') as f:
        return set(line.strip() for line in f.readlines())

# Save new job URLs to file
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
                continue  # Skip already sent

            comp = card.find('a', class_='subTitle').text.strip()
            exp = card.find('li', class_='experience').text.strip()
            post_date = card.find('span', class_='footer').text.lower()

            # Check if posted within 1 day
            if not any(keyword in post_date for keyword in ['1 day ago', 'today', 'few hours']):
                continue

            if str(TARGET_EXPERIENCE) not in exp:
                continue

            jobs.append({'title': title, 'company': comp, 'link': link, 'exp': exp, 'location': city})
        except:
            continue

    return jobs

def get_all_jobs(seen_jobs):
    all_jobs = []
    for city in CITIES:
        jobs = fetch_naukri_jobs(city, seen_jobs)
        all_jobs.extend(jobs)
    return all_jobs

def create_linkedin_message(job):
    return (f"Hi [Hiring Manager],\n"
            f"I came across the {job['title']} role at {job['company']} in {job['location']}. "
            "With ~3 years of experience in GCP — BigQuery, Dataflow, Airflow and Python — "
            "I’d love to connect and explore how I can support your data engineering goals.\nThanks,\n[Your Name]")

def create_email_body(jobs):
    if not jobs:
        return "<p>No new jobs found today.</p>"
    body = "<h2>🚀 GCP Data Engineer Jobs – Hyderabad & Chennai (Posted Today)</h2>"
    for job in jobs:
        body += f"""
        <h3>{job['title']} @ {job['company']} – {job['location']}</h3>
        <p><strong>Experience:</strong> {job['exp']}</p>
        <p><a href="{job['link']}">Apply Now</a></p>
        <p><strong>LinkedIn Outreach:</strong><br>{create_linkedin_message(job).replace('\n', '<br>')}</p>
        <hr>
        """
    return body

def send_email(html_body):
    yag = yagmail.SMTP("your_email@gmail.com", "your_app_password")
    yag.send(
        to="your_email@gmail.com",
        subject=f"GCP Data Engineer Jobs – {time.strftime('%b %d, %I:%M %p')}",
        contents=html_body
    )

if __name__ == "__main__":
    seen = load_seen_jobs()
    new_jobs = get_all_jobs(seen)
    if new_jobs:
        send_email(create_email_body(new_jobs))
        save_seen_jobs([job['link'] for job in new_jobs])
    else:
        print("✅ No new jobs found today.")
