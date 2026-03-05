#!/usr/bin/env python3
"""Notify subscribers of new blog posts via AgentMail."""

import json
import os
import sys

AGENTMAIL_API = "https://agentapi.io/v1/message"
AGENTMAIL_KEY = os.environ.get("AGENTMAIL_API_KEY", "")

def load_subscribers():
    """Load subscribers list."""
    try:
        with open('subscribers.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_sent_posts():
    """Load list of posts already sent to subscribers."""
    try:
        with open('sent_posts.json', 'r') as f:
            return json.load(f)
    except:
        return []

def save_sent_posts(posts):
    """Save list of sent posts."""
    with open('sent_posts.json', 'w') as f:
        json.dump(posts, f)

def get_latest_article():
    """Get the most recent article from stream-data.json."""
    try:
        with open('stream-data.json', 'r') as f:
            data = json.load(f)
            articles = data.get('articles', [])
            if articles:
                return articles[0]
    except Exception as e:
        print(f"Error loading articles: {e}")
    return None

def notify_subscriber(email, article):
    """Send email notification to subscriber via AgentMail."""
    if not AGENTMAIL_KEY:
        print("No AGENTMAIL_API_KEY set, skipping notification")
        return False
    
    import urllib.request
    import urllib.parse
    
    subject = f"New post from Katsuma: {article.get('title', 'New Article')}"
    body = f"""Hi! 

There's a new blog post on Katsuma's website:

{article.get('title', 'New Article')}

{article.get('excerpt', '')}

Read more: https://meetkatsuma.live/blog

---
You're receiving this because you subscribed to updates from https://meetkatsuma.live
"""
    
    data = json.dumps({
        "to": email,
        "message": body,
        "subject": subject
    }).encode()
    
    req = urllib.request.Request(
        AGENTMAIL_API,
        data=data,
        headers={
            "Authorization": f"Bearer {AGENTMAIL_KEY}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"Notified {email}: {result}")
            return True
    except Exception as e:
        print(f"Error notifying {email}: {e}")
        return False

def main():
    """Check for new articles and notify subscribers."""
    print("Checking for new articles to notify subscribers...")
    
    subscribers = load_subscribers()
    if not subscribers:
        print("No subscribers to notify")
        return
    
    article = get_latest_article()
    if not article:
        print("No articles found")
        return
    
    sent_posts = load_sent_posts()
    article_id = article.get('id')
    
    if article_id in sent_posts:
        print(f"Article {article_id} already sent to subscribers")
        return
    
    print(f"New article found: {article.get('title')}")
    
    for email in subscribers:
        notify_subscriber(email, article)
    
    # Mark as sent
    sent_posts.append(article_id)
    save_sent_posts(sent_posts)
    print(f"Notified {len(subscribers)} subscribers about {article_id}")

if __name__ == "__main__":
    main()
