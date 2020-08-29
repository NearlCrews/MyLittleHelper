# MyLittleHelper
A PRAW Reddit bot to assist with moderation. 

# Summary
Quick overview of the major functions of the bot:
1. **Editorilized headlines:** compare the submitted post headline to the "real" post headline, look for a configurable difference, and leave a notice if they don't match up. 
2. **Abuse of the report function:** count the number of reports in a thread, compare it to a configurable threshold, and leave a reminder if the number of reports exceeds the total.
3. **Ignore certain reports:** automatically approve report types that you don't care about.
4. **New account greeter:** send a message to a user in the subreddit when they're posting with a new account.

Be gentle. I'm still new to Python and I'm sure there are more efficient ways of doing everything. This was a "COVID-19 I'm bored" learning project. Either way, it seems to work as expected and we're receiving actionable information.

# Installation
Install the required modules:
```
pip3 install --upgrade configparser bs4 praw
```

You want to plug the correct values into `settings.ini`. They're fairly simple:
```
[general]
# General settings across all of the modules.
# Bot username and password, or use your own.
reddit_user = 
reddit_pass = 
# Create the secret OATH values. Instructions on Reddit.
reddit_client_id = 
reddit_client_secret = 
# Bot owner. This is typically your username. Don't add the u/ in front of the name.
bot_owner = 
# Subreddit to monitor, e.g. Michigan.
reddit_target_subreddit = 

[alteredheadline]
# This alerts when a user is posting a headline that differs from the real headline.
# Turn on the module. Leave blank for false.
enable = True
# Score for how "different" the topic and submissions are. High number = more identical from 0-100.
score_threshold = 50
# Set to true if you'd like the bot to leave a comment on the post. Leave blank for false.
leave_post_comment = True
# Set to true if you'd like a mod notice sent to the subreddit. Leave blank for false.
leave_mod_notice =
# Include the full markdown link to the rule being violated. For example:
# [Rule #6](https://www.reddit.com/r/YourSubreddit/wiki/index#wiki_rules)
link_to_rule = 
# Regex for domains to ignore. This is often because their headlines are broken.
ignore_domains = (?:.*bloomberg\.com.*|.*reddit\.com.*|.*redd\.it.*|.*imgur\.com.*|.*youtube\.com.*|.*wikipedia\.org.*|.*twitter\.com.*|.*youtu\.be.*|.*facebook\.com.*)

[reportabuse]
# Remind people that the report button is not a super-downvote.
# Turn on the module. Leave blank for false.
enable = True
# Total number of comment reports before the notice is posted.
total_report_threshold = 5
# Set to true if you'd like the bot to leave a comment on the post. Leave blank for false.
leave_post_comment = True
# Link to the rules. Include the full markdown link to the rule being violated. For example:
# [The subreddit rules can be found here.](https://www.reddit.com/r/YourSubreddit/wiki/index#wiki_rules)
link_to_rules = 

[ignorereport]
# Ignore those reports that you just don't care about.
# Turn on the module. Leave blank for false.
enable = True
# Regex of the report type to ignore. Case insensitive.
ignore_regex = (?:.*Example1.*|.*Example2.*)

[newaccount]
# Sending a greeting to new accounts that posted for the first time. It only sends one.
# Turn on the module. Leave blank for false. 
enable = True
# Age in days for the new account.
new_account_age = 1
# Link to subreddit rules. Include the full markdown link to the rule being violated. For example:
# [subreddit rules](https://www.reddit.com/r/YourSubreddit/wiki/index#wiki_rules)
subreddit_rules = 

[flairmanager]
# Add and remove flair based on account age.
# Turn on the module. Leave blank for false.
enable = True
# Red flag accounts under this age in days. Default of 30 days.
age_floor = 30
# Award accounts over this age in days. Default of 10 years.
age_ceiling = 3650
# Floor Template ID
# Create a template ID for the floor and ceiling.
# Don't worry about the text, it's just for the text and background colors.
age_floor_template =
age_ceiling_template =
```

You then simply run the bot:
`python3 MyLittleHelper.py`

I run it in `screen` since I'm usually watching the ouput. 

**Sample Notice For Altered Headlines:**
```
Hello u/XXXXXX!

The title of your post differs from the actual article title and has been flagged for review. Please review Rule #6 in the r/Michigan subreddit rules. If this is an actual rule violation, you can always delete the submission and resubmit with the correct headline. Otherwise, this will likely be removed by the moderators. Please note that some websites change their article titles and this may be a false-positive. In that case, no further action is required. Further details:

Posted Title: Hmmmm.

Actual Title: No spike in coronavirus in places reopening, U.S. health secretary says - AOL News

Similarity: 2%

Please contact u/YYYYYY if this bot is misbehaving.
```

**Sample Notice for Report Abuse:**
```
Hello! This is an automated reminder that the report function is not a super-downvote button. Reported comments are manually reviewed and may be removed if they are an actual rule violation. Please do not report comments simply because you disagree with the content. Abuse of the report function is against the site rules and will be reported.

The subreddit rules can be found here.

I'm a bot and will not reply. Please contact u/YYYYYY if this bot is misbehaving.
```

**Sample Greeting for New Users:**
```
Hello u/XXXXXX!

I'm a purpose-built bot that assists in moderating r/YourSubreddit. It appears that you are commenting in r/YourSubreddit with an account that is less than 1 day old. Please take a moment to read the subreddit rules and let the moderators know if you have any questions. This will be the only automated message that you receive from me.

I'm a bot and will not reply. Please contact u/YYYYYY if this bot is misbehaving.
```

**Flair Management:***
This will add "Age Flair" to new accounts to help spot trolls. It also adds an flair for accounts that have been around for a long time.
