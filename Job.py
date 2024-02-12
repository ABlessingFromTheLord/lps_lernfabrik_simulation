class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration

    # getters
    def get_name(self):
        return self.name

    def get_duration(self):
        return self.duration
