import requests
from bs4 import BeautifulSoup
import yagmail
import time
import os

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

    print(f"🔎 Found {len(job_cards)} total job cards on page")

    for card in job_cards:
        try:
            title_tag = card.find('a', class_='title')
            title = title_tag.text.strip()
            link = title_tag['href']
            comp = card.find('a', class_='subTitle').text.strip()
            exp = card.find('li', class_='experience').text.strip()
            post_date = card.find('span', class_='footer').text.lower()

            print(f"📄 Title: {title}\n   Company: {comp}\n   Exp: {exp}\n   Posted: {post_date}\n   Link: {link}\n")

            # Collect all jobs, even seen or old ones
            jobs.append({
                'title': title,
                'company': comp,
                'link': link,
                'exp': exp,
                'location': city
            })

        except Exception as e:
            print(f"⚠️ Error parsing job card: {e}")
            continue

    return jobs

def get_all_jobs(seen_jobs):
    all_jobs = []
    for city in CITIES:
        print(f"\n🌆 Searching jobs in {city}...")
        jobs = fetch_naukri_jobs(city, seen_jobs)
        print(f"✅ Found {len(jobs)} new jobs in {city}")
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
    body = "<h2>🚀 GCP Data Engineer Jobs – Hyderabad & Chennai (Posted Recently)</h2>"
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
    yag = yagmail.SMTP("lakshmivarikallu.work@gmail.com", "afve oypz uroq iami")
    yag.send(
        to="lakshmivarikallu.work@gmail.com",
        subject=f"GCP Data Engineer Jobs – {time.strftime('%b %d, %I:%M %p')}",
        contents=html_body
    )

if __name__ == "__main__":
    seen = load_seen_jobs()
    new_jobs = get_all_jobs(seen)
    if new_jobs:
        print("📧 Sending email with new jobs...")
        send_email(create_email_body(new_jobs))
        save_seen_jobs([job['link'] for job in new_jobs])
    else:
        print("✅ No new jobs found today.")
