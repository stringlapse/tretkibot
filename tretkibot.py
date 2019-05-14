#!/usr/bin/python3

import praw, datetime, time, pytz, random, string, obot
from messages import *

#  --------
#  Settings
#  --------

subreddit = "XXXXX" # Subreddit to add users to
botUsername = "XXXXX" # Username of the bot
writeLogs = True # Wether or not to write logs to a file
logFile = "XXXXX" # Path to write logs to if writeLogs == True
randomFlairs = False # Wether or not to randomize member flairs on each run
immunity = [] # Members we don't want to kick without confirmation
memberCap = 95 # How many members we want in the subreddit
bannedSubs = [] # Subreddits we don't want users from
bannedUsers = [] # Users we don't want in the sub
karmaDownLimit = 100  # Minimum comment karma
karmaUpLimit = 100000000  # Maximum comment karma
accountAgeLimit = 30 # Minimum account age in days
wordsLimit = []  # Words we don't want in a username

# --------

#today = str(datetime.datetime.now().day) + "-" + str(datetime.datetime.now().month) + "-" + str(datetime.datetime.now().year)
#now = datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=-7), 'Mountain Standard Time'))
now = datetime.datetime.now(pytz.timezone('US/Mountain'))
today = str(now.day) + "-" + str(now.month) + "-" + str(now.year)

def log(m):
    print(m)
    if writeLogs:
        logs = open(logFile + today + ".txt", "a")
        logs.write(m + "\n")
        logs.close()

recap = ""

# Sign in as bot user
log("Signing in as /u/" + botUsername + "...")
try:
    r = obot.login()
except:
    print("Wrong username/password combination")
else:
    s = r.subreddit(subreddit)
    log("Done")

# Set up functions
def kick(user):
    s.contributor.remove(user)
    flair(user,"[Kicked]",'kicked')
    log("Kicked " + user)

def add(user):
    s.contributor.add(user)
    log("Added " + user)

def getUserList():
    userList = []
    for contributor in r.subreddit(subreddit).contributor():
        username = str(contributor)
        if username != botUsername:
            userList.append(username)
    userList.reverse()
    return userList

def flair(user,flair,css):
    s.flair.set(user, flair,css_class='css')
    log("/u/"+user+"'s flair changed to '"+flair+"' (CSS "+css+")")

def postRecap(m):
    log("Posting the recap...")
    postTitle = str(today) +' - Bot Recap'
    r.subreddit(subreddit).submit(postTitle, m)
    log("Done")

def confirmAction():
    m = input().lower()
    if m == "y":
        return True
    elif m == "n":
        return False
    else:
        print("Unrecognized input, assuming N")
        return False

# Kick inactive users
memberList = getUserList()
recap += "Kicked users: \n\n"

log("Starting to kick inactive members...")

i = 0
n = 0

for member in memberList:
        i+=1
        log("#" + str(i) + " /u/" + member)

        overview = r.redditor(member).new(limit=None)

        latestPost = 50000.0 #hours
        hoursLimit = 180.0 #hours

        for post in overview:
                postedSub = post.subreddit.display_name
                hoursAgo = (time.time()-post.created_utc)/3600.0

                if postedSub == subreddit:
                        if hoursAgo < latestPost:
                                latestPost = hoursAgo

                if hoursAgo>hoursLimit:
                        break

        if latestPost <= hoursLimit:
                log("[OK] Latest post was " + str(latestPost) + " hours ago.")
        else:
                log("[NOT OK] No post in /r/" + subreddit + " in the last 7 days.")
                if member in immunity:
                    log("/u/" + member + " is in immunity list. Kick anyway? [Y/N]")
                    if confirmAction() == False:
                        log("/u/" + member + " will not be kicked")
                        continue
                    else:
                        log("/u/" + member + " has been kicked")
                recap += r"\#" + str(i) + " - /u/" + member + "\n\n"
                n+=1
                kick(member)

# Add new members
nbAdded = memberCap-len(memberList)+n
log("Adding " + str(nbAdded) + " users...")
newUser = ""
recap += "\nAdded users:  \n\n"
sourceList = []

if nbAdded<0:
        nbAdded=0

while nbAdded>0:
        for c in r.subreddit("all").comments():
                username = str(c.author)
                linkId = c.link_id.replace("t3_","")+"/"+c.id
                karma = c.author.comment_karma
                postedSub = c.subreddit.display_name
                accountAge = (time.time()-c.author.created_utc)/86400.0

                log("Considering /u/" + username + " from post " + linkId + ".")

                if username in bannedUsers:
                        log("[NOT OK] Banned user.")
                        continue

                if postedSub in bannedSubs:
                        log("[NOT OK] Posted in a banned subreddit")
                        continue

                if karma < karmaDownLimit:
                        log("[NOT OK] Comment karma too low.")
                        continue

                if karma > karmaUpLimit:
                        log("[NOT OK] Comment karma too high.")
                        continue

                if accountAge < accountAgeLimit:
                        log("[NOT OK] Account too recent.")
                        continue

                if any(word in username for word in wordsLimit):
                        log("[NOT OK] Username contains banned word.")
                        continue

                if random.randint(0,1) == 1:
                        log("[NOT OK] Not lucky enough.")
                        continue

                sourceList.append({'user':username,'sourcePost':c.link_id.replace("t3_",""),'sourceComment':c.id,'sourceSubreddit':postedSub})

                nbAdded-=1

                print(nbAdded)
                add(username)

                if newUser == "":
                        newUser = username

                if nbAdded==0:
                        break

# Add new members to recap
new=""
i=0
newUsers = []
for user in getUserList():
        i+=1

        if user == newUser:
                new = 'new'

        if new=="new":
                newUsers.append(user)
                for x in sourceList:
                        if user == x['user']:
                                sourcePost_ = x['sourcePost']
                                sourceComment_ = x['sourceComment']
                                sourceSubreddit_ = x['sourceSubreddit']
                                break
                recap += r"\#" + str(i) + " - /u/" + user + ' from [this comment](https://reddit.com/comments/' + sourcePost_ + '/comment/' + sourceComment_ + '?context=10000) in [r/' + sourceSubreddit_ + '](https://reddit.com/r/' + sourceSubreddit_ + ')\n\n'

#Update member flairs
if not randomFlairs:
    i=0
    for user in getUserList():
        i+=1
        flair(user,'#'+str(i),'number'+new)

if randomFlairs:
    userList = getUserList()
    numbers = []
    for i in range(1, len(userList)+1):
        numbers.append(i)
    for user in userList:
        number = numbers[random.randint(0,len(numbers)-1)]
        flair(user,'#'+str(number),'number'+new)
        numbers.remove(number)

# Add welcome message to recap
if random.randint(0,1) == 1:
        recap += '-----\n\n' + welcomeMessages[random.randint(0,len(welcomeMessages)-1)]
else:
        pickedUser = newUsers[random.randint(0,len(newUsers)-1)]
        recap += '-----\n\n' + userWelcomeMessages[random.randint(0,len(userWelcomeMessages)-1)].format(pickedUser)

# Post recap
postRecap(recap)
