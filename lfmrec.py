#!/usr/bin/python

# Audioscrobbler/Last.fm Recommendations
# Chris Coykendall
# Dependencies: pylast

import pylast
import recommendations
import sys
from math import sqrt


# Global test API strings
API_KEY='584407af429a648663d4c9195f7a584e'
API_SECRET='116c6e60adf9efedfc346aacb0dc904a'


# Global API handler
try:
    network = pylast.LastFMNetwork(API_KEY, API_SECRET)
except:
    print 'Couldn\'t establish network connection. Try again later.'
    sys.exit(0)


# Get friends of a user based on user name
# user: Name of user | numFriends: # of friends to fetch
def getFanFriends(username,numFriends):

    try:
        user = network.get_user(username)
        userlist = user.get_friends(limit=numFriends)
    except:
        print 'Couldn\'t retrieve user. Please check name/connection or try again later.'
        sys.exit(0)
    
    # Add themselves to the list
    userlist.append(user)
    return userlist


# Get a usable recommendation data set from Audioscrobbler user 
# list based on the number of plays for particular artists, ie assume
# the more a fan listens to an artist, the more likely they would
# recommend them.
# userList: List of fans to generate 2nd order dictionary
def getArtistPlaysDataSet(userList):

    listenMatrix={}
    uCount=0
    for user in userList:
        uCount = uCount+1
        uName=str(user)
        listenMatrix[uName]={}

        # Get the most played artists for this user (default 50)
        try:
            artistList = user.get_top_artists()
        except:
            print 'Couldn\'t retrieve user. Please check name/connection or try again later.'
            sys.exit(0)
        # Handle funky characters in user names for prettier output
        for artist in artistList:
            listenMatrix[uName][artist.item.name.encode('ascii','ignore')]=float(artist.weight)
        print 'Fetched ' + str(len(artistList)) + ' artists from ' + uName + '(' + str(uCount) + '/' + str(len(userList))+ ')...'
        listenMatrix[uName] = normalizePlayCounts(listenMatrix[uName])
        
    return listenMatrix


# Normalize play counts to a usable scale through Z-distribution w/ curve
# artistList: A list of artists/listen weight pairs
def normalizePlayCounts(artistList):
    # Determine mean
    sumPlays=0
    for artist in artistList:
        curWeight = artistList[artist]
        sumPlays = sumPlays + curWeight
    if len(artistList)==0:
        return artistList
    avgPlays = sumPlays / len(artistList)

    # Calculate standard deviations
    stdDevSum = 0.0
    for artist in artistList:
        stdDevSum=stdDevSum+pow(artistList[artist]-avgPlays,2)
    stdDev = sqrt(stdDevSum/len(artistList))
    maxVal=-99999
    minVal=99999
    for artist in artistList:
        if stdDev==0:
            artistList[artist]=0
        else:
            artistList[artist] = (((artistList[artist] - avgPlays) / stdDev))

        # Collect range of data
        if artistList[artist]>maxVal:
            maxVal=artistList[artist]
        elif artistList[artist]<minVal:
            minVal=artistList[artist]
    
    # If no plays for any artist, avoid division by zero
    if not (maxVal==0 and minVal==0):
        for artist in artistList:        
            # Make minimum 0 and maximum 1
            artistList[artist] = artistList[artist]+abs(minVal)/maxVal+abs(minVal)

            # Apply simple curve for better distribution, scale to 5 and cast to float
            artistList[artist] = float(pow(artistList[artist],1.7)*3+1)
            if artistList[artist]>5:
                artistList[artist]=5
    return artistList




# Main Menu
# Use the web services API to get a set of data for making and building a
# music recommendation system.
def main():
    print 'Audioscrobbler/Last.fm Recommendations by Chris Coykendall  '
    print '------------------------------------------------------------'
    if network:

        # Get user to recommend to
        user=raw_input('Enter user to recommend to: ')
        # DEBUG user='chinabuffet'

        numFriends=raw_input('Enter # of friends to collect listen data from: ')

        print 'Fetching Last.fm API data for ' + user + '...'    

        # Get the fan's friends
        friends=getFanFriends(user,int(numFriends))
        if friends==None:
            return

        print 'Retrieved ' + str(len(friends)-1) + ' friends from ' + user + '...'

        # Get the fan and friends top artists based on relative number of artist plays
        print 'Fetching most listened artists from user and their friends...'
        fanArtistData=getArtistPlaysDataSet(friends)

        # Use similarity to determine top 5 similar users based on artists played
        closestMatches= recommendations.topMatches(fanArtistData,user,5)
        print '>>>>> Top 5 Similar Users out of ' + str(len(closestMatches)) + ' friends:'
        for match in closestMatches[:5]:
            print match[1] + ' (' + str(round(((match[0]+1)/2)*100,1)) + '%)'
        print '<<<<<'

        # Use Pearson score to determine top 20 recommended artists for user from friends listens
        recArtists= recommendations.getRecommendations(fanArtistData,user)
        print '>>>>> Top 20 Recommended Artists out of ' + str(len(recArtists))
        sumIt=0
        for match in recArtists[:20]:
            print match[1] + ' (' + str(round(match[0]*20,1)) + '%)'
        print '<<<<<'

        # Ask whether or not to display the data set
        if raw_input('Would you like to display the data dictionary (Y/N)?: ').upper()=='Y':
            for user in fanArtistData:
                    print user
                    for artist in fanArtistData[user]:
                        print '\t' + artist + ': ' + str(round(fanArtistData[user][artist],1))
        

# Call main process function
main()
raw_input("Press any key to close...")

