class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, part_name, duration, machine, machine_codename):
        self.name = name
        self.part_name = part_name
        self.duration = duration
        self.job_before = Job
        self.job_after = Job
        self.machine_required = machine
        self.machine_codename = machine_codename
        self.completed = 0
        self.depth = None
        self.amount_produced = 0

    # getters
    def get_name(self):
        return self.name

    def get_part_name(self):
        return self.part_name

    def get_duration(self):
        return self.duration

    def get_job_before(self):
        return self.job_before

    def get_job_after(self):
        return self.job_after

    def get_machine_required(self):
        return self.machine_required

    def get_machine_codename(self):
        return self.machine_codename

    def get_completed(self):
        return self.completed

    def get_depth(self):
        return self.depth

    def get_amount_produced(self):
        return self.amount_produced

    # setters
    def set_job_before(self, job):
        self.job_before = job

    def set_job_after(self, job):
        self.job_after = job

    def set_completed(self, value):
        self.completed = value

    def set_depth(self, value):
        self.depth = value

    def set_amount_produced(self, value):
        self.amount_produced = value
