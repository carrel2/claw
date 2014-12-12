#!/usr/local/bin/python2

import sys
import os
import paramiko
import git
import logging
import smtplib
from email.mime.text import MIMEText

passwordFlag = False

def suppressPasswords( configInfo ):
        #Called when script is run with -p flag.
        #Needs to look through the config file generated and remove
        #passwords and other sensitive information. Should be
        #independent of the machine.

        return configInfo

def checkFormat( output=False ):
        try:
                file = open( 'claw.conf', 'r' )

                contents = file.read()

                leftBracketList = findAll( contents, '{' )
                rightBracketList = findAll( contents, '}' )

                if len( leftBracketList ) != len( rightBracketList ):
                        if output:
                                print "Missing a bracket"

                        return False

                for index in range( len( leftBracketList ) - 1 ):
                        if leftBracketList[index + 1] < rightBracketList[index]:
                                if output:
                                        print "Misplaced left bracket '{'"

                                return False

                        if rightBracketList[index + 1] < leftBracketList[index]:
                                if output:
                                        print "Misplaced right bracket '}'"

                                return False

                file.close()

                if output:
                        print "All good"

                return True

        except IOError:
                print "Couldn't find claw.conf!"
                return False

def findAll( string, substring ):
        i = 0
        indexlist = []
        index = string.find( substring )

        while i >= 0:
                if i != 0:
                        indexlist.append( i )

                i = string.find( substring, i + 1 )

        return indexlist

def clawMachines( debug=False ):
        try:
                repo = git.Repo( os.getcwd() )
        except git.exc.InvalidGitRepositoryError:
                repo = git.Repo.init( os.getcwd() )

        rows, columns = os.popen( 'stty size', 'r' ).read().split()
        index = repo.index
        file = open( 'claw.conf', 'r' )

        fromAddress = file.readline()[:-1]
        toAddress = file.readline()[:-1]
        subject = file.readline()[:-1]

        blockNumber = 0
        logMessage = ''

        while file.readline():
                hosts = file.readline()[:-1].split( ',' )
                username = file.readline()[:-1]
                password = file.readline()[:-1]
                command = file.readline()[:-1]
                commands = []

                blockNumber += 1

                while command != '}':
                        if command != '' and command != '{':
                                commands.append( command.strip() )

                        command = file.readline()[:-1]

                for host in hosts:
                        client = paramiko.SSHClient()

                        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                        try:
                                client.connect( host, username=username, password=password )

                                if debug:
                                        print
                                        print ''.center( int( columns ), '#' )
                                        print host.center( int( columns ), ' ' )
                                        print ''.center( int( columns ), '#' )
                                        print

                                for command in commands:
                                        stdin, stdout, stderr = client.exec_command( command )

                                        if debug:
                                                print "Running:", command
                                                print
                                                print stdout.read()
                                        else:
                                                configFileName = host + "-" + command.replace( " ", "-" )
                                                configFile = open( configFileName, 'w' )

                                                if passwordFlag:
                                                        configFile.write( suppressPasswords( stdout.read() ) )
                                                else:
                                                        configFile.write( stdout.read() )

                                                configFile.close()

                                                index.add( [configFileName] )

                                client.close()

                        except Exception, e:
                                if debug:
                                        print
                                        print "claw.conf block", blockNumber
                                        print host
                                        print e
                                else:
                                        logging.basicConfig( filename='claw.log', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M' )

                                        logging.warning( 'In block %s: %s: %s', blockNumber, host, e )
                                        logMessage += 'In block ' + str( blockNumber ) + '\n' + host + ': ' + str( e ) + '\n\n'

        file.close()

        if not debug:

                diff = repo.git.diff( '--staged' )

                s = smtplib.SMTP( 'localhost' )

                if diff:
                        index.commit( configFileName )
                        message = MIMEText( diff )

                        message['From'] = fromAddress
                        message['To'] = toAddress
                        message['Subject'] = subject

                        s.sendmail( fromAddress, [toAddress], message.as_string() )

                if logMessage != '':
                        message = MIMEText( logMessage )

                        message['From'] = fromAddress
                        message['To'] = toAddress
                        message['Subject'] = 'CLAW errors'

                        s.sendmail( fromAddress, [toAddress], message.as_string() )

                s.quit()

        else:
                print

##                     ##
# End of clawMachines() #
##                     ##

if '-p' in sys.argv:
        passwordFlag = True

if '-c' in sys.argv:
        checkFormat( output=True )
elif '-d' in sys.argv and checkFormat():
        clawMachines( debug=True )
elif checkFormat():
        clawMachines()
