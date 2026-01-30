class LanguageProfile:
    def __init__(
        self,
        code: str,
        name: str,
        script: str,
        sentence_order: str,
        articles: bool,
        cases: bool,
        genders: int,
        politeness: bool,
    ):
        self.code = code
        self.name = name
        self.script = script
        self.sentence_order = sentence_order
        self.articles = articles
        self.cases = cases
        self.genders = genders
        self.politeness = politeness
