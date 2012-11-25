CONNECT = """
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
"""

AREAS = {
    "North America": (5, ["Alaska", "Northwest Territories", "Greenland", "Alberta", "Ontario", "Quebec", "Western United States", "Eastern United States", "Mexico"]),
    "South America": (2, ["Venezuala", "Brazil", "Peru", "Argentina"]),
    "Africa": (3, ["North Africa", "Egypt", "East Africa", "Congo", "South Africa", "Madagascar"]),
    "Europe": (5, ["Iceland", "Great Britain", "Scandanavia", "Ukraine", "Northern Europe", "Western Europe", "Southern Europe"]),
    "Asia": (7, ["Middle East", "Afghanistan", "India", "South East Asia", "China", "Mongolia" ,"Japan", "Kamchatka" ,"Irkutsk", "Yakutsk", "Siberia", "Ural"]),
    "Australia": (2, ["Indonesia", "New Guinea", "Eastern Australia", "Western Australia"])
}

MAP = """
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
KEY = {
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

