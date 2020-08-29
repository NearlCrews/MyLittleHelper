#####
# Import everything.
#####
import praw
import configparser
import requests
from bs4 import BeautifulSoup
import re
import difflib
import time
from pprint import pprint
from datetime import datetime, timedelta, date
import time
from prawcore.exceptions import Forbidden

# Version 2.0

# Set DEBUG
DEBUG = True

#####
# Read the configuration.
#####
# General.
config = configparser.ConfigParser()
config.read('settings.ini')
reddit_user = str(config['general']['reddit_user'])
reddit_pass = str(config['general']['reddit_pass'])
reddit_client_id = str(config['general']['reddit_client_id'])
reddit_client_secret = str(config['general']['reddit_client_secret'])
reddit_target_subreddit = str(config['general']['reddit_target_subreddit'])
bot_owner = str(config['general']['bot_owner'])

# AlteredHeadline.
ah_score_threshold = int(config['alteredheadline']['score_threshold'])
ah_leave_post_comment = bool(config['alteredheadline']['leave_post_comment'])
ah_leave_mod_notice = bool(config['alteredheadline']['leave_mod_notice'])
ah_link_to_rule = str(config['alteredheadline']['link_to_rule'])
ah_ignore_domains = str(config['alteredheadline']['ignore_domains'])
ah_enable = bool(config['alteredheadline']['enable'])

# ReportAbuse.
ra_total_report_threshold = int(config['reportabuse']['total_report_threshold'])
ra_leave_post_comment = bool(config['reportabuse']['leave_post_comment'])
ra_enable = bool(config['reportabuse']['enable'])
ra_link_to_rules = str(config['reportabuse']['link_to_rules'])

# IgnoreReports.
ir_report_regex = str(config['ignorereport']['ignore_regex'])
ir_enable = bool(config['ignorereport']['enable'])

# NewAccounts.
na_new_account_age = int(config['newaccount']['new_account_age'])
na_enable = bool(config['newaccount']['enable'])
na_subreddit_rules = str(config['newaccount']['subreddit_rules'])

# FlairManager
fm_enable = bool(config['flairmanager']['enable'])
fm_age_floor = int(config['flairmanager']['age_floor'])
fm_age_ceiling = int(config['flairmanager']['age_ceiling'])
fm_age_floor_template = str(config['flairmanager']['age_floor_template'])
fm_age_ceiling_template = str(config['flairmanager']['age_ceiling_template'])

#####
# Set a few variables.
#####
# Regex list of domains to ignore.
drop_urls = re.compile(ah_ignore_domains, re.IGNORECASE)

# Regex for reports to ignore.
ir_ignore_reports = re.compile(ir_report_regex, re.IGNORECASE)

# Regex for URL validity.
valid_url = re.compile('(?:^http.*)', re.IGNORECASE)

print(f'!CONFIG!\nConfiguration has been read.\n')

#####
# Create the Reddit object and streams.
#####
# Create the Reddit object.
reddit = praw.Reddit(
    username=reddit_user,
    password=reddit_pass,
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent='MyLittleHelper managed by u/{}'.format(bot_owner)
)

# Create the streams.
try:
  comment_stream = reddit.subreddit(reddit_target_subreddit).stream.comments(pause_after=-1)
  submission_stream = reddit.subreddit(reddit_target_subreddit).stream.submissions(pause_after=-1)
  report_stream = reddit.subreddit(reddit_target_subreddit).mod.stream.reports(pause_after=-1)
except Exception as e:
  print(e)

print(f'!CONFIG!\nReddit object and streams have been initialized.\n')

# Start the streaming loop for new submissions.
while True:

#####
# This block is for dealing with submissions.
#####
  try:
    for submission in submission_stream:

      # Break if there's nothing new.
      if submission is None:
        break

      try:
        #####
        # AlteredHeadline
        #####
        if ah_enable:
          # Ignore self-posts and cross-posts:
          if submission.is_self or submission.num_crossposts > 0 or submission.saved:
            continue

          # Ensure it starts with http* and drop bad domains.
          if not valid_url.match(submission.url) or drop_urls.match(submission.url):
            if not submission.saved:
              submission.save()
            continue

          # Find the real title from the actual HTML.
          headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}
          real_url_request = requests.get(submission.url, headers=headers, timeout=5)
          html_content = real_url_request.text
          soup = BeautifulSoup(html_content, 'html.parser')
          # Check to make sure we get a real value and remove any extra characters.
          if type(soup.title) == type(None):
            if not submission.saved:
              submission.save()
            continue
          else:
            real_title = soup.title.string.strip()
          # Ignore short URL titles since the website isn't returning a title.
          if len(real_title) <= 16:
            if DEBUG:
              print(f'!ALTEREDHEADLINE!\nSkipping and saving this one since it has a short title.\n')
            if not submission.saved:
              submission.save()
            continue

          # Convert to lowercase and identify similarity.
          similarity_object = difflib.SequenceMatcher(None, submission.title.lower(), real_title.lower())
          similarity = round(similarity_object.ratio()*100)
          if DEBUG:
            print(f'!ALTEREDHEADLINE!\nUsername: {submission.author} \nSubmitted URL: {submission.url} \nPost Title: {submission.title} \nActual Title: {real_title} \nSimilarity: {similarity}\n')
          if (similarity >= ah_score_threshold):
            if not submission.saved:
              submission.save()
            continue

          # Send an alert if the title differs significantly.
          if similarity <= ah_score_threshold and ah_leave_mod_notice:
            n_link = '[Link to post for review.]({})\n\n'.format(submission.permalink)
            n_posted = '**Posted Title:** {}\n\n'.format(submission.title)
            n_actual = '**Actual Title:** {}\n\n'.format(real_title)
            n_similarity = '**Similarity:** {}%\n\n'.format(similarity)
            n_footer = '\n\n*Please contact u/{} if this bot is misbehaving.*\n\n'.format(bot_owner)
            notification = n_actual + n_posted + n_similarity + n_link + n_footer
            reddit.subreddit(reddit_target_subreddit).message('Potentially Altered Headline', notification)
            if DEBUG:
              print(f'!ALTEREDHEADLINE!\nLeaving mod notice on \"{submission.title}\"\n')
            if not submission.saved:
              submission.save()

          # Leave a comment in the thread.
          if similarity <= ah_score_threshold and ah_leave_post_comment:
            r_message = 'Hello u/{}!\n\n The title of your post differs from the actual article title and has been flagged for review. Please review {} in the r/{} subreddit rules. If this is an actual rule violation, you can always delete the submission and resubmit with the correct headline. Otherwise, this will likely be removed by the moderators. Add `?repost` to the end of the URL if you receive an error about the link already being submitted. Please note that some websites change their article titles and this may be a false-positive. In that case, no further action is required. Further details: \n\n'.format(submission.author, ah_link_to_rule, reddit_target_subreddit)
            n_posted = '**Posted Title:** {}\n\n'.format(submission.title)
            n_actual = '**Actual Title:** {}\n\n'.format(real_title)
            n_similarity = '**Similarity:** {}%\n\n'.format(similarity)
            n_footer = '\n\n*Please contact u/{} if this bot is misbehaving.*\n\n'.format(bot_owner)
            comment_text = r_message + n_posted + n_actual + n_similarity + n_footer
            post_submission = reddit.submission(id=submission.id)
            this_comment = post_submission.reply(comment_text)
            this_comment.mod.distinguish(how='yes')
            if DEBUG:
               print(f'!ALTEREDHEADLINE!\nLeaving user comment on \"{submission.title}\"\n')
            if not submission.saved:
              submission.save()

      except:
        continue

  #####
  # This block is for dealing with comments.
  #####

    for comment in comment_stream:
      if comment is None:
        break

      try:
        #####
        # FlairManager
        #####
        if fm_enable:
          # Get the user, creation date, and age in days of the account.
          fm_user = reddit.redditor(comment.author)
          fm_creation_date = date.fromtimestamp(fm_user.created_utc)
          fm_account_age = int((int(time.time()) - int(fm_user.created_utc))/(24*60*60))
          # Look for accounts less than the floor-defined age.
          if int(fm_account_age) <= int(fm_age_floor):
            if DEBUG:
              print(f'!FLAIRMANAGER FLOOR!\nFlairManager:\nUser: {comment.author}\nAccount age: {fm_account_age}\n')
            # Chunk them into < 3 days.
            if fm_account_age <= 3:
              fm_age_text = "Age: < 3 Days"
              try:
                reddit.subreddit(reddit_target_subreddit).flair.set(comment.author, text=fm_age_text, flair_template_id=fm_age_floor_template)
              except Forbidden as e:
                print(e)
                continue
            # Get anything less than the defined floor.
            else:
              fm_age_text = 'Age: {} Days'.format(fm_account_age)
              try:
                reddit.subreddit(reddit_target_subreddit).flair.set(comment.author, text=fm_age_text, flair_template_id=fm_age_floor_template)
              except Forbidden as e:
                print(e)
                continue

          # Clear the flare on anyone between the floor and ceiling.
          if (int(fm_account_age) > int(fm_age_floor)) and (int(fm_account_age) <= int(fm_age_ceiling)):
            if comment.author_flair_text.startswith('Age: '):
              try:
                print(f'!FLAIRMANAGER CLEARING FLAIR!\nFlairManager:\nUser: {comment.author}\nAccount age: {fm_account_age}\nFlair Text: {comment.author_flair_text}\n')
                reddit.subreddit(reddit_target_subreddit).flair.delete(comment.author)
              except Forbidden as e:
                print(e)
                continue
          
          # Look for the OG accounts above the ceiling. 
          if int(fm_account_age) >= int(fm_age_ceiling):
            if DEBUG:
              flair_length = len(str(comment.author_flair_text))
              print(f'!FLAIRMANAGER CEILING!\nFlairManager:\nUser: {comment.author}\nAccount age: {fm_account_age}\nFlair length: {flair_length}\n')
            if len(str(comment.author_flair_text)) <= 4:
              try:
                fm_age_text = "Age: > 10 Years"
                reddit.subreddit(reddit_target_subreddit).flair.set(comment.author, text=fm_age_text, flair_template_id=fm_age_ceiling_template)
                print(f'!FLAIRMANAGER OG FLAIR ADDED!\nFlairManager:\nUser: {comment.author}\nAccount age: {fm_account_age}\n')
              except Forbidden as e:
                print(e)
                continue

        #####
        # NewAccount
        #####
        if na_enable:
          na_daysAgoSeconds = int(time.time()) - (60*60*24*na_new_account_age)
          na_user = reddit.redditor(comment.author)
          na_creation_date = date.fromtimestamp(na_user.created_utc)
          if int(na_user.created_utc) > int(na_daysAgoSeconds):
            if DEBUG:
              print(f'!NEWACCOUNT!\nUser: {comment.author}\nAccount creation date: {na_creation_date}\nComment: {comment.body}\n')
            if not na_user.is_friend:
              # Use "day" or "days".
              if na_new_account_age == 1:
                day_text = "day"
              else:
                day_text = "days"
              na_message_text = 'Hello u/{}!\n\nI\'m a purpose-built bot that assists in moderating r/{}. It appears that you are commenting in r/{} with an account that is less than {} {} old. Please take a moment to read the {} and let the moderators know if you have any questions. This will be the only automated message that you receive from me.\n\n*I\'m a bot and will not reply. Please contact u/{} if this bot is misbehaving.*'.format(comment.author, reddit_target_subreddit, reddit_target_subreddit, na_new_account_age, day_text, na_subreddit_rules, bot_owner)
              # Add them as a friend so we only do this once.
              reddit.redditor(str(comment.author)).friend()
              # Send the message.
              reddit.redditor(str(comment.author)).message("Greetings!", na_message_text)
              if DEBUG:
                print(f'!NEWACCOUNT!\nGreeting sent to user: {comment.author}\nAccount creation date: {na_creation_date}\nComment: {comment.body}\n')

      except:
        continue

  #####
  # This block is for dealing with reports.
  #####

    for report in report_stream:
      if report is None:
        break

      try:
        #####
        # ReportAbuse
        #####
        if ra_enable:
          # Set the counter to zero.
          ra_total_reports = 0
          ra_skip_post = False
          # Get the post submission.
          ra_post_submission = reddit.submission(url=report.link_permalink)

          # Get all of the comments for the post.
          ra_post_submission.comments.replace_more(limit=None)

          # Walk through the comments.
          for ra_comment in ra_post_submission.comments.list():
            # Check if a mod has been here.
            if ra_comment.distinguished:
              print(f'!REPORTABUSE!\nDistinguished comment found. Assuming a moderator was here.\n')
              # Keep loop sanity and just tell it not to post here later.
              ra_skip_post = True
            # Find and count any reported comments.
            if ra_comment.num_reports != 0:
              ra_total_reports += 1
              if DEBUG:
                print(f'!REPORTABUSE!\nCurrent report count: {ra_total_reports}\nURL: {report.link_permalink}\n')
          if int(ra_total_reports) >= int(ra_total_report_threshold) and not ra_skip_post:
            if DEBUG:
              print(f'!REPORTABUSE!\nNotice Triggered.\n{report.link_permalink}\n{report.link_title}\n')
            ra_comment_text = 'Hello! This is an automated reminder that the report function is not a super-downvote button. Reported comments are manually reviewed and may be removed *if they are an actual rule violation*. Please do not report comments simply because you disagree with the content. Abuse of the report function is against the site rules and will be reported.\n\n{}\n\n*I\'m a bot and will not reply. Please contact u/{} if this bot is misbehaving.*'.format(ra_link_to_rules, bot_owner)
            ra_this_comment = ra_post_submission.reply(ra_comment_text)
            ra_this_comment.mod.distinguish(how='yes', sticky=True)
            # Give them comment time to register for future loops.
            time.sleep(5)

        #####
        # IgnoreReport
        #####
        if ir_enable:
          ir_user_reports = " ".join(str(x) for x in report.user_reports)
          if ir_ignore_reports.match(ir_user_reports):
            if DEBUG:
              print(f'!IGNOREREPORT!\n{ir_user_reports}\n')
            ir_comment = reddit.comment(report.id)
            ir_comment.mod.approve()
            ir_post = reddit.submission(id=report.id)
            ir_post.mod.approve()

      except:
        continue

  except Exception as e:
    print(e)
    # Wait a while and try again.
    print("Error in main loop. Will try again in 5 minutes.")
    time.sleep(300)
    continue
