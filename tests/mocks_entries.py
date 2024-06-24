
class MockEntries:
    def __init__(self, entries):
        self.entries = entries

    def as_gitlab_users(self, _glb, login_column):
        for entry in self.entries:
            yield entry, None

class MockEntriesFactory:
    def __init__(self):
        pass

    def create(self, entries):
        return MockEntries(entries)
