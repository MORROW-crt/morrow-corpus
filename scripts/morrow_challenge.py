#!/usr/bin/env python3
"""Conservative Moltbook arithmetic decoder. No external model or network usage.

Only solve a limited, unambiguous family of arithmetic word problems.
Fail closed if the text, operands or operation is ambiguous. One verification
attempt at most; never guess after a failure.
"""
from __future__ import annotations
import difflib
import re
from decimal import Decimal

UNITS = {
    "zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,
    "seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,
    "thirteen":13,"fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,
    "eighteen":18,"nineteen":19,"twenty":20,"thirty":30,"forty":40,
    "fifty":50,"sixty":60,"seventy":70,"eighty":80,"ninety":90,
    "hundred":100,"thousand":1000,
}
SPELLINGS = tuple(UNITS)

def normalize(text):
    if type(text) is not str or len(text) > 600 or len(text) < 15:
        raise ValueError("Invalid challenge length")
    # Embedded punctuation is noise in Moltbook maths challenges.
    return re.findall(r"[a-z]+|\d+(?:\.\d+)?", re.sub(
        r"[^a-zA-Z0-9.\s]", "", text).lower())

def number_word(token):
    if token in UNITS:
        return token
    # Obfuscation introduces doubled letters and occasional misspellings.
    if len(token) < 4: return None
    c = difflib.get_close_matches(token, SPELLINGS, n=2, cutoff=.82)
    if len(c) != 1:return None
    return c[0]

def simplify(tokens):
    """Join short broken fragments only when the joined string is a number."""
    clean=[]
    i=0
    while i<len(tokens):
        if i+1<len(tokens) and len(tokens[i])>=2 and len(tokens[i+1])<=3:
            joined=tokens[i]+tokens[i+1]
            word=number_word(joined)
            if word and word not in ("one","two") and (len(tokens[i+1])<=2 or len(tokens[i])<=3):
                clean.append(word);i+=2;continue
        clean.append(tokens[i]);i+=1
    return clean

def extract_numbers(tokens):
    found=[]
    i=0
    while i<len(tokens):
        t=tokens[i]
        if t.replace(".","",1).isdigit():
            found.append((Decimal(t),i));i+=1;continue
        word=number_word(t)
        if word is None or word in ("hundred","thousand"):
            i+=1;continue
        amount=UNITS[word]
        j=i+1
        if amount in range(20,100,10) and j<len(tokens):
            nxt=number_word(tokens[j])
            if nxt and UNITS[nxt] in range(1,10):
                amount+=UNITS[nxt];j+=1
        if j<len(tokens) and number_word(tokens[j])=="hundred":
            amount*=100;j+=1
            if j<len(tokens):
                nxt=number_word(tokens[j])
                if nxt and 0<UNITS[nxt]<100:
                    amount+=UNITS[nxt];j+=1
        found.append((Decimal(amount),i))
        i=j
    return found

def solve(challenge_text):
    tokens=simplify(normalize(challenge_text))
    found=extract_numbers(tokens)
    if len(found)!=2:
        raise ValueError("Expected exactly two unequivocal operands; found "+str(len(found)))
    left,right=(found[0][0],found[1][0])
    normalized=" ".join(tokens)
    subtract=any(phrase in normalized for phrase in ("slows","slowed","slow down","slows down",
        "decrease","drops by","loses","lost","minus","subtract","less than","reduced by"))
    multiply=any(phrase in normalized for phrase in ("per pinch","per claw","each claw",
        "each pinch","two pinches","times","multiplied","product","double","twice",
        "number of pinches","for every"))
    add=any(phrase in normalized for phrase in ("speeds up","speed up","increases","increase",
        "gains","more than","together","total","combined","sum of","adds","plus",
        "both claws","other claw"))
    # Phrases such as "total force" specify the requested result of a
    # per-pinch multiplication; do not treat that alone as a second operation.
    if multiply and add and not any(phrase in normalized for phrase in
        ("other claw","both claws","plus","together","combined","sum of","adds")):
        add=False
    flags=sum([subtract,multiply,add])
    # Accept explicit maths operators only if the text contains exactly two numbers
    # and an unambiguous operation, never based on noise punctuation alone.
    if flags!=1:
        raise ValueError("Ambiguous or unsupported operation")
    if subtract:
        value=left-right
    elif multiply:
        value=left*right
    else:
        value=left+right
    if abs(value)>Decimal("100000000") or value.as_tuple().exponent < -3:
        raise ValueError("Unsupported magnitude")
    return f"{value.quantize(Decimal('0.01')):.2f}"

if __name__=="__main__":
    import sys
    print(solve(" ".join(sys.argv[1:])))
