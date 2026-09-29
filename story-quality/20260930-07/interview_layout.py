"""Exact interview-card recognition; ordinary mentions remain ordinary narration."""
import re
TITLE=re.compile(r'[\s―—–\-－ー─]*(?:取材記録|采访记录|取材记录|取材録)[\s―—–\-－ー─]*')

def is_interview_marker(text):
 if not isinstance(text,str) or not text:return False
 plain=re.sub(r'\[text(?:Black|Red|Blue|Yellow):([^\]]*)\]',r'\1',text,flags=re.S)
 plain=re.sub(r'</?(?:black|red|blue|yellow)>','',plain,flags=re.I)
 first=re.split(r'@|\\n|\r?\n|\[br\]',plain,maxsplit=1)[0].strip()
 return TITLE.fullmatch(first) is not None

def interview_names(cleaned):
 # Preserve legacy visible card content and spelling, including color wrappers.
 result=[]
 for part in cleaned.split('\\n'):
  value=re.sub(r'\[textBlack:(.*?)\]',r'\1',part).strip()
  if value and not any(t in value for t in ('记录','記録','―')):result.append(value)
 return result
