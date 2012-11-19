from pyrisk import Game
import sys
import os
import optparse
import random

try:
  import psyco
  psyco.profile()
  print "Using PSYCO"
except:
  pass
  

gamemap = """
Alaska--Northwest Territories--Alberta--Alaska
Alberta--Ontario--Greenland--Northwest Territories
Greenland--Quebec--Ontario--Eastern United States--Quebec
Alberta--Western United States--Ontario--Northwest Territories
Western United States--Eastern United States--Mexico--Western United States

Venezuala--Peru--Argentina--Brazil
Peru--Brazil--Venezuala

North Africa--Egypt--East Africa--North Africa
North Africa--Congo--East Africa--South Africa--Congo
East Africa--Madagascar--South Africa

Indonesia--Western Australia--Eastern Australia--New Guinea--Indonesia
Western Australia--New Guinea

Iceland--Great Britain--Western Europe--Southern Europe--Northern Europe--Western Europe
Northern Europe--Great Britain--Scandanavia--Northern Europe--Ukraine--Scandanavia--Iceland
Southern Europe--Ukraine

Middle East--India--South East Asia--China--Mongolia--Japan--Kamchatka--Yakutsk--Irkutsk--Kamchatka--Mongolia--Irkutsk
Yakutsk--Siberia--Irkutsk
China--Siberia--Mongolia
Siberia--Ural--China--Afghanistan--Ural
Middle East--Afghanistan--India--China

Mexico--Venezuala
Brazil--North Africa
Western Europe--North Africa--Southern Europe--Egypt--Middle East--East Africa
Southern Europe--Middle East--Ukraine--Afghanistan--Ural
Ukraine--Ural
Greenland--Iceland
Alaska--Kamchatka
South East Asia--Indonesia

[North America,5]Alaska,Northwest Territories,Greenland,Alberta,Ontario,Quebec,Western United States,Eastern United States,Mexico
[South America,2]Venezuala,Brazil,Peru,Argentina
[Africa,3]North Africa,Egypt,East Africa,Congo,South Africa,Madagascar
[Europe,5]Iceland,Great Britain,Scandanavia,Ukraine,Northern Europe,Western Europe,Southern Europe
[Asia,7]Middle East,Afghanistan,India,South East Asia,China,Mongolia,Japan,Kamchatka,Irkutsk,Yakutsk,Siberia,Ural
[Australia,2]Indonesia,New Guinea,Eastern Australia,Western Australia
"""
cursemap="""
  aa       bbbb b         cccccc          pp     tB B BCCCCCDDDDDDDDFFFF       
 aaaaaaabbbbbbbbbb        cccc           ppptt tttBBBBBCCCCCDDDDDDDFFFFFFFFFFF 
 aaaaaaabbbbbbbbbbb       ccc   nnn     pp pttttttBBBBBCCCCCDDDDDFFFFFFFFFFFF F
 aaaaaaaaddddddde   fff    c        o  pp  tttttttBBBBBCCCEEEEEEEFFFFFFFFFF    
  a     adddddddeee  fff           oo   p rtttttttBBBBBCCEEEEEEEEFFF    F      
        adddddddeeeefffff          ooo rrrrtttttGGGGBBBCCEEEEHHHHHFFF          
          ddddddeeeeffff f           qqrrrrtttttGGGGGGBIIIIHHHHHHHHH           
          ggggggghh ffff             qqsssss ttt GGGGGGIIIIIHHHHHHHH           
          ggggggghhhhh             qqq ss ss tt  GGGGGGIIIIIIIIIII  J          
           gggggghhhh              qq   s ssAAAAAAKKKGGIIIIIIIII I JJ          
           gggghhhhhh               uuuu     AAAAAKKKKKKIIIIIIII  JJ           
            ggghhh h               uuuuuuvvvvAAA AKKKKKKKIIIIIII  J            
              ii                  uuuuuuuvvvv AAAA  KKKKKKLLLLII               
              ii                  uuuuuuuvvvvv AAA   KKKK LLLL                 
               iii                uuuuuuuuwwww AA     KK  LLL                  
                  iiijj           uuuuuuuuwwwww       K     L   M              
                    jjjjj          uuuuuuxxwwwww       K   M   MM  NN          
                    kjjjmmmm            uxxwww              MMMM  NNNN          
                    kkmmmmmmmm          xxxwww                       N         
                     kkkmmmmm           xxxyyy zz                PPPP          
                      lkkmmmm           yyyyy  z               OOPPPPP         
                      lllll              yyyy  z              OOOOOPPPP        
                      llll               yyy                   OOOOPPPP        
                      lll                yy                    OO  PPPP        
"""
cursekey={
"a": "Alaska",
"b": "Northwest Territories",
"c": "Greenland",
"d": "Alberta",
"e": "Ontario",
"f": "Quebec",
"g": "Western United States",
"h": "Eastern United States",
"i": "Mexico",
"j": "Venezuala",
"k": "Peru",
"l": "Argentina",
"m": "Brazil",
"n": "Iceland",
"o": "Great Britain",
"p": "Scandanavia",
"q": "Western Europe",
"r": "Northern Europe",
"s": "Southern Europe",
"t": "Ukraine",
"u": "North Africa",
"v": "Egypt",
"w": "East Africa",
"x": "Congo",
"y": "South Africa",
"z": "Madagascar",
"A": "Middle East",
"B": "Ural",
"C": "Siberia",
"D": "Yakutsk",
"E": "Irkutsk",
"F": "Kamchatka",
"G": "Afghanistan",
"H": "Mongolia",
"I": "China",
"J": "Japan",
"K": "India",
"L": "South East Asia",
"M": "Indonesia",
"N": "New Guinea",
"O": "Western Australia",
"P": "Eastern Australia",
}

names = ['ALPHA','BRAVO','CHARLIE','DELTA','ECHO','FOXTROT','GOLF','HOTEL','INDIA','JULIET','KILO','LIMA','MIKE','NOVEMBER','OSCAR','PAPA','QUEBEC','ROMEO','SIERRA','TANGO','UNIFORM','VICTOR','WHISKEY','XRAY','YANKEE','ZULU']

parser = optparse.OptionParser(usage='Usage: python %prog [opts] AIName AIName...')
parser.add_option('-x','--no-curses',dest='curses',action='store_false',default=True,help='Disable ncurses UI')
parser.add_option('-c','--curses-colors',dest='curses_colors',action='store_true',default=False,help='Allow ncurses to use colors')
parser.add_option('-d','--dot',dest='dot',action='store_true',default=False,help='Allow DOT output')
parser.add_option('-p','--dot-prefix',dest='dot_prefix',action='store',help='Prefix for dot files')
parser.add_option('-s','--stdout',dest='stdout',action='store_true',default='False',help='Output to stdout')
parser.add_option('-l','--logfile',dest='logfile',action='store',help='Name of logfile to produce')
parser.add_option('-n','--games',dest='n',action='store',type='int',default=1,help='Number of games to run')
parser.add_option('-w','--wait',dest='pause',action='store_true',default=False,help='Pause after each action')

options,ais = parser.parse_args()

ai_modules = {}
ai_names = []
ai_history = {}
options.player_history = ai_history
options.map = gamemap
options.cursemap = cursemap
options.cursekey = cursekey
for i,ai in enumerate(ais):
  ai_modules[ai]=__import__(ai,fromlist=[ai])
  ai_names.append(random.choice(names))
  names.remove(ai_names[-1])
  ai_history[ai_names[-1]]=0

results = []  
for i in xrange(options.n):
  game = Game(**options.__dict__)
  for i,ai in enumerate(ais):
    game.addPlayer(ai_names[i],getattr(ai_modules[ai],ai)())
  result = game.startGame()
  del game
  results.append(result)
  ai_history[result['winner']]+=1
  
winner_count = {}
turns = []  

for result in results:
  if result['winner'] in winner_count:
    winner_count[result['winner']] += 1
  else:
    winner_count[result['winner']] = 1
  turns += [result['turns']]
    
print
print "====WINNER STATS===="
print
for winner in winner_count:
  print "%s\t%s\t%s" % (winner,ais[ai_names.index(winner)], winner_count[winner])

print
print "====TURN STATS===="
print
print "Minimum Turns %s Maximum Turns %s Average Turns %.2f" % (min(turns),max(turns),float(sum(turns))/options.n)
print