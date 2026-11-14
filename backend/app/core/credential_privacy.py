"""Deterministic credential boundaries. No provider, database, or logging I/O."""
import re
import unicodedata

MASK = "\u2022"*12
GENERATED_HISTORY = "Generated Password: shown only in the immediate response; value not saved."
WORDS = set(("why what how is are was were can should the this that my your a an good bad strong weak "
    "safe safer secure insecure password passwords passphrase pwd make makes generate create produce "
    "suggest give please new random another again for me and or in with without "
    "better best practices policy policies manager length entropy character characters symbol symbols "
    "number numbers uppercase lowercase check analyze analyse test rate score audit crack cracked tell "
    "explain about long longer short shorter easy simple complex predictable considered strength "
    "of it its do does secret token credential credentials").split())
CONTEXT = re.compile(r"\b(?:password|passphrase|pwd|credential|secret)\w*\b|"
                     r"\b(?:strong|weak|insecure|guessable|entropy|strength)\b",re.I)
LABEL = re.compile(r"\b(?:password|passphrase|pwd|secret)\s*(?:is\s+|[:=]\s*)"
                   r"(?P<value>\"[^\"]+\"|'[^']+'|\x60[^\x60]+\x60|\u201c[^\u201d]+\u201d|\u2018[^\u2019]+\u2019|[^\s]+)",re.I)
QUOTED = re.compile(r"\"([^\"]+)\"|'([^']+)'|\x60([^\x60]+)\x60|\u201c([^\u201d]+)\u201d|\u2018([^\u2019]+)\u2019")
TRAILING = re.compile(r"\b(?:password|passphrase|pwd)\s+(?P<value>[^\s]+)\s*$",re.I)


def folded(value):
    return "".join(c for c in unicodedata.normalize("NFKC",value)
                   if unicodedata.category(c)!="Cf").casefold()


def _mapped(value):
    chars,positions = [],[]
    for index,c in enumerate(value):
        if unicodedata.category(c)=="Cf":
            continue
        for normalized in unicodedata.normalize("NFKC",c).casefold():
            chars.append(normalized);positions.append(index)
    return "".join(chars),positions


def credential_candidates(text):
    """Return original values/spelling; normalization is detection-only."""
    normalized,positions = _mapped(text)
    contextual = bool(CONTEXT.search(normalized))
    result = []
    def original(start,end):
        if start>=end:
            return ""
        left=min(positions[start],positions[start-1]+1) if start else 0
        right=positions[end] if end<len(positions) else len(text)
        return text[left:right]
    def add(value):
        if value and value not in result:
            result.append(value)
    # A previously generated value may be pasted back without a password label.
    unlabeled=[]
    # Scan alphabet runs rather than whitespace tokens: surrounding commas,
    # full stops and Unicode punctuation must not send pasted values to models.
    # Mask padded runs in full too, rather than exposing a long token's suffix.
    for match in re.finditer(r"[A-Za-z0-9!@#$%^&*()_=+\[\]{}?\-]{8,}",text):
        value=match.group()
        if all((
            any(c.isupper() for c in value),any(c.islower() for c in value),
            any(c.isdigit() for c in value),any(not c.isalnum() for c in value))):
            unlabeled.append(value)
    if not contextual:
        return tuple(unlabeled)
    for match in LABEL.finditer(normalized):
        value = original(*match.span("value"))
        if len(value)>1 and value[0] in "\"'\x60\u201c\u2018" and value[-1] in "\"'\x60\u201d\u2019":
            value=value[1:-1]
        add(value)
    for match in QUOTED.finditer(normalized):
        group=next(i for i in range(1,6) if match.group(i) is not None)
        add(original(*match.span(group)))
    match=TRAILING.search(normalized)
    if match and match["value"].strip(".,;:!?") not in WORDS:
        add(original(*match.span("value")))
    strength_value = re.compile(
        r"\b(?:is|was)\s+(?P<value>[^\s]+)\s+(?:(?:a|an|considered|too)\s+)*"
        r"(?:strong|weak|insecure|guessable)\b|\bstrength\s+of\s+(?P<other>[^\s]+)", re.I)
    for match in strength_value.finditer(normalized):
        group="value" if match.group("value") is not None else "other"
        value=original(*match.span(group))
        if folded(value).strip(".,;:!?") not in WORDS:
            add(value)
    for match in re.finditer(r"\S+",normalized):
        word=match.group().strip(".,;:!?\"'\x60()[]{}\u201c\u201d\u2018\u2019")
        if word in WORDS or len(word)<4 or word.startswith(("http://","https://")):
            continue
        value=original(*match.span()).strip("\"'\x60\u201c\u201d\u2018\u2019")
        if (any(c.isdigit() for c in word) and any(c.isalpha() for c in word)) or \
           any(not c.isalnum() for c in word):
            add(value)
    # Explicit original values take priority over alphabet-run substrings.
    for value in unlabeled:
        add(value)
    return tuple(result)


def redact_credentials(text, extra=()):
    values = set(credential_candidates(text)) | {v for v in extra if v}
    for value in sorted(values,key=len,reverse=True):
        text=text.replace(value,MASK)
    return text


def history_topics(messages):
    """Only fixed labels may leave legacy history; raw transcripts never do.

    Omit credential-related thread context, even outside the last-eight window.
    Database/display history is intact.
    """
    contents=[str(m.content or "") for m in messages]
    if any(CONTEXT.search(folded(value)) or credential_candidates(value) for value in contents):
        return ()
    labels=[]
    topics=(
        ("zero trust","zero trust"),("tls","TLS"),("certificate","TLS"),
        ("incident","incident response"),("ransomware","ransomware"),
        ("sql injection","SQL injection"),("csrf","CSRF"),("cve","vulnerability management"),
        ("firewall","firewalls"),("backup","backup recovery"),("nist","NIST guidance"),
        ("authentication","authentication"),("phishing","phishing"),
    )
    for value in contents[-8:]:
        lower=folded(value)
        for needle,label in topics:
            if re.search(r"\b"+re.escape(needle)+r"\b",lower) and label not in labels:
                labels.append(label)
    return tuple(labels)

def persisted_answer(text, question=None):
    """No credential-bearing model reply is used as a stored transcript."""
    if text==GENERATED_HISTORY:
        return text
    if (question and CONTEXT.search(folded(question))) or re.search(
            r"(?:generated|suggested.*strong)\s+password",folded(text)):
        return GENERATED_HISTORY if "generated" in folded(text) else "Password response: shown only in the immediate response."
    return redact_credentials(text)
