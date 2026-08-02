class IntentClassifier:

    @staticmethod
    def classify(question: str) -> str:

        q = question.lower()

        if "cve-" in q or "cve " in q:
            return "threat"

        if any(word in q for word in [
            "password",
            "passphrase",
            "credential",
        ]):
            return "password"

        if any(word in q for word in [
            "http://",
            "https://",
            "url",
            "domain",
            "website",
        ]):
            return "url"

        return "knowledge"