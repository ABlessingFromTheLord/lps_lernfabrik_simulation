class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, duration, part_made_before, part_to_be_made_after):
        self.name = name
        self.duration = duration
        self.part_made_before = part_made_before
        self.part_to_be_made_after = part_to_be_made_after

    # getters
    def get_name(self):
        return self.name

    def get_duration(self):
        return self.duration

    def get_part_made_before(self):
        return self.part_made_before

    def get_part_to_be_made_after(self):
        return self.part_to_be_made_after

    # setters
    def set_part_made_before(self, part_name):
        self.part_made_before = part_name

    def set_part_to_be_made_after(self, part_name):
        self.part_to_be_made_after = part_name