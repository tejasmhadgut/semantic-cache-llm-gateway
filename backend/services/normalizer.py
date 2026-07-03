
import re
import string


def normalize(text: str) -> str:
    text = text.lower()
    filler_phrases = [
        "can you",
        "could you",
        "would you",
        "will you",
        "please",
        "tell me",
        "show me",
        "i want to know",
        "i'd like to know",
        "give me",
        "find me",
        
    ]
    for phrase in filler_phrases:
        text = re.sub(rf"\b{re.escape(phrase)}\b","",text)
    
    text = text.translate(str.maketrans("","", string.punctuation))
    text = re.sub(r"\s+"," ",text);
    return text.strip()
    

