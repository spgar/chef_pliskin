# chef_pliskin is a reddit bot that offers an optinion of the doneness of food.

import praw
import sqlite3
import time
import obot

conversionChart = {
    'rare': 'medium rare',
    'medium rare': 'medium',
    'medium-rare': 'medium',
    'medium': 'medium well'
}

reponse = 'Looks {0} to me.'
waitTime = 60 * 10 # Runs every 10 minutes

# Open the SQL database
print 'Opening SQL database connection.'
sql = sqlite3.connect('chef_pliskin.db')
cursor = sql.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS commentedsubmissions(id TEXT)')

# Connect to reddit
print 'Connecting to Reddit'
r = praw.Reddit(obot.app_ua)
r.set_oauth_app_info(obot.app_id, obot.app_secret, obot.app_uri)
r.refresh_access_information(obot.app_refresh)

def shouldReplyToSubmission(submission):
    # We're only interested in submissions that are images from imgur
    if 'imgur' not in submission.url:
        return False

    # ... that includes one of the words in conversionChart in the title...
    if not any(s in submission.title.lower() for s in conversionChart.keys()):
        return False

    # ... and isn't a submission that we've commented on before.
    cursor.execute('SELECT * FROM commentedsubmissions WHERE ID=?', [submission.id])
    if cursor.fetchone():
        return False

    return True

def createResponseComment(submission):
    matches = [s for s in conversionChart if s in submission.title.lower()]
    return reponse.format(conversionChart[matches[0]])

def replyToSubmission(submission):
    print 'Replying to this submission: ', submission.title
    comment = createResponseComment(submission)
    print 'With this comment: ', comment

    submission.add_comment(comment);

    # Update our database so that we don't reply to this submission again
    cursor.execute('INSERT INTO commentedsubmissions VALUES(?)', [submission.id])
    sql.commit()

def runBot():
    print 'chef_pliskin is looking for matching submissions.'
    subreddit = r.get_subreddit('food')
    for submission in subreddit.get_new(limit=500):
        if shouldReplyToSubmission(submission):
            replyToSubmission(submission)

# Run the bot logic in a loop
keepRunning = True
while keepRunning:
    try:
        runBot()
        print "chef_pliskin has finished looking. Will search again in {0} seconds.".format(waitTime)
        time.sleep(waitTime)
    except Exception as e:
        print "Some exception happened, so we're shutting down."
        print e
        keepRunning = False
