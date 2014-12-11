#!/usr/local/bin/python2

import sys
import paramiko
import git
import smtplib
from email.mime.text import MIMEText

passwordFlag = False

def suppressPasswords( configFile ):
        #Called when script is run with -p flag.
        #Needs to look through the config file generated and remove
        #passwords and other sensitive information. Should be
        #independent of the machine.

        pass

def checkFormat( output=False ):
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

def findAll( string, substring ):
        i = 0
        indexlist = []
        index = string.find( substring )

        while i >= 0:
                if i != 0:
                        indexlist.append( i )

                i = string.find( substring, i + 1 )

        return indexlist

def clawMachines():
        repo = git.Repo( "/home/carrel2" )
        index = repo.index
        file = open( 'claw.conf', 'r' )

        fromAddress = file.readline()[:-1]
        toAddress = file.readline()[:-1]
        subject = file.readline()[:-1]

        while file.readline():
                hosts = file.readline()[:-1].split( ',' )
                username = file.readline()[:-1]
                password = file.readline()[:-1]
                commands = []

                while file.readline()[:-1] != '}':
                        commands.append( file.readline()[:-1] )

                for host in hosts:

                        client = paramiko.SSHClient()

                        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        client.connect( host, username=username, password=password )

                        for command in commands:
                                configFileName = host + "-" + command.replace( " ", "-" )
                                configFile = open( configFileName, 'w' )

                                stdin, stdout, stderr = client.exec_command( command )

                                configFile.write( stdout.read() )

                                if passwordFlag:
                                        suppressPasswords( configFile )

                                configFile.close()

                                index.add( [configFileName] )

                        client.close()

        file.close()

        diff = repo.git.diff( '--staged' )

        if diff:
                index.commit( configFileName )
                message = MIMEText( diff )

                message['From'] = fromAddress
                message['To'] = toAddress
                message['Subject'] = subject

                s = smtplib.SMTP( 'localhost' )
                s.sendmail( fromAddress, [toAddress], message.as_string() )
                s.quit()

##                     ##
# End of clawMachines() #
##                     ##

if '-c' in sys.argv:
        checkFormat( output=True )
elif '-p' in sys.argv and checkFormat():
        passwordFlag = True
        clawMachines()
elif checkFormat():
        clawMachines()
