import requests
import tweepy
import os
import openai
import re
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")
OPENAI_KEY = os.getenv("OPENAI_KEY")
TEMPERATURE = 0.85

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)
openai.api_key = OPENAI_KEY

try:
  api.verify_credentials()
  print("Authentication OK")
except:
  print("Error during authentication")

#try to follow more accounts in the top 1000 (twitter rate limits following new accounts)
def follow_users(): 
  file = open("top_1000_users.txt", "r", encoding="utf-8")
  names = [i.split(",")[0] for i in file]
  for name in names:
    try:
      #Remove the user from the list of users to work through to prevent slowdown and api calls
      with open("top_1000_users.txt", "r", encoding="utf-8") as users:
        data = users.read().splitlines()
      with open("top_1000_users.txt", "w", encoding="utf-8") as rewrite:
        rewrite.write("\n".join(data[1:]) + "\n")
      #try to friend the user. If rate limited, break and post. If not found, doesn't matter, already erased, keep going. 
      api.create_friendship(screen_name=name)
    except tweepy.errors.Forbidden as e:
      print(e)
      print("follow rate limit reached")
      break
    except tweepy.errors.NotFound as e:
      print(e)
      print("User Not Found. Skipping")

#isolated into a function to make it easy to skip during testing.
follow_users()

#get tweets and format them into a prompt
tweet_list = api.home_timeline(count=20)
string = ""
#skip retweets
for index, tweet in enumerate(tweet_list):
  if tweet.text[0:2] == "RT":
    continue
  string += f"{index+1}. {tweet.text}\n"

#request a text completion from openai
completion = openai.Completion.create(engine = "davinci", temperature = TEMPERATURE,  prompt = string, max_tokens = 800, stop = "\n")
completion_text = completion.choices[0].text

#if the completion contains a "4. " or "21. " etc at the beginning because of the prompt format, remove it
found = re.search(r"\d+\.\s+", completion_text)
if found:
  completion_text = completion_text[len(found.group(0)):]

#if the URL contains a dead link tweepy will throw at 408 - Given URL is invalid
found = re.search(r"https:\/\/t.co\/\S+", completion_text)
if found:
  completion_text = completion_text.replace(found.group(0), "")

#post the text!
print(f"Posting: {completion_text}")
#api.update_status(completion_text)