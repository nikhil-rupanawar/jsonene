class RequiredDependency:
    def __init__(self, source, targets):
        self.source = source
        self.targets = targets

    def to_schema(self):
        return {self.source: self.targets}
