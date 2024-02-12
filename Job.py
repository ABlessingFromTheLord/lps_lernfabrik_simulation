import simpy


class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, part_name, duration, machine):
        self.name = name
        self.part_name = part_name
        self.duration = duration
        self.job_before = Job
        self.job_after = Job
        self.machine_required = machine
        self.completed = False

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

    def get_completed(self):
        return self.completed

    # setters
    def set_job_before(self, job):
        self.job_before = job

    def set_job_after(self, job):
        self.job_after = job

    def set_completed(self, boolean):
        self.completed = boolean


