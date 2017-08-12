import math

#2  Write a function, string_time, that takes three inputs,
#   the number of hours, minutes, and seconds since midnight,
#   and returns a string that represents the time in 12 hour 
#   format with AM or PM at the end. 
#
#   If the input is larger than a single day (or is for the
#   previous day) you should print an error and return an
#   empty string.
#
#   If the input represents midnight or noon, you should return
#   "Midnight" or "Noon" instead of "12:00:00 AM" or "12:00:00 PM"
#
#   For example, string_time(0, 0, 1) should return "12:00:01 AM"
#   and string_time(23, 0, 0) should return "11:00:00 PM"
def min_sec_pad(value):
    if value < 10:
        return "0" + str(value)
    else:
        return str(value)

def string_time(hours, minutes, seconds):
    if hours > 23 or minutes > 59 or seconds > 59 or hours < 0 \
        or minutes < 0 or seconds < 0:
        return "invalid input"
    
    if hours >= 12:
        label = "PM"
    else:
        label = "AM"

    if hours == 0:
        hours = 12
    elif hours > 12:
        hours -= 12
        
    if hours == 12 and minutes == 0 and seconds == 0:
        if label == "AM":
            return "Midnight"
        else:
            return "Noon"
    
    return str(hours) + ":" + min_sec_pad(minutes) + ":" + min_sec_pad(seconds) \
        + " " + label

#3  Write a function, blackjack2, that takes 2 cards as input 
#   and returns the highest value of a blackjack hand with those 
#   2 cards in it.
#
#   In blackjack, number cards are worth their face value,
#   face cards are worth 10 and and Ace can be worth 1 or 11.  You
#   choose the value of the Ace to make the value of the hand as
#   high as possible without going over 21.
#
#   As the suit is irrelevant, assume that each card is represented
#   as a single character from the string "23456789TJQKA"
#
#   Look in the docs for various functions on strings that might
#   be useful.
#
#   For example, blackjack2("5", "K") should return 15.
def card_to_val(card):
    if card in "23456789":
        return int(card)
    elif card in "TJQK":
        return 10
    else:
        return 11
    
def val_with_ace(other_card_val):
    if other_card_val < 11:
        return 11 + other_card_val
    else:
        return 1 + other_card_val
    
def blackjack2(card1, card2):
    if card1 == "A":
        return val_with_ace(card_to_val(card2))
    elif card2 == "A":
        return val_with_ace(card_to_val(card1))
    else:
        return card_to_val(card1) + card_to_val(card2)

#4  Write a function, blackjack3, that takes 3 cards as input 
#   and returns the highest value of a blackjack hand with those 
#   3 cards in it.  The result should not be greater than 21, if
#   that is possible.
#
#   Think carefully about how this is different than blackjack2.
#
#   For example, blackjack3("5", "K", "5") should return 20.
def blackjack3(card1, card2, card3):
    total_val = card_to_val(card1) + card_to_val(card2) + card_to_val(card3)
    
    if (card1 == "A" or card2 == "A" or card3 == "A") and total_val > 21:
        ## Count the ace as a 1 instead of an 11
        total_val -= 10
        
        if total_val > 21:
            ## There must be another ace; with only one ace, counted as a 1,
            ## the max is 1 + 10 + 10 = 21
            total_val -= 10
            
    return total_val
