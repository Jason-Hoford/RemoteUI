"""Profile configuration — equivalent to Java's Profile.java."""


class Profile:
    def __init__(self, api_level: int, operations_profiles: int, platform=None):
        self.api_level = api_level
        self.operations_profiles = operations_profiles
        self.platform = platform
