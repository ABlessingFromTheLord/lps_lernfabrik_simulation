class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, duration):
        self.name = name
        self.duration = duration
        self.job_before = Job
        self.job_after = Job

    # getters
    def get_name(self):
        return self.name

    def get_duration(self):
        return self.duration

    def get_job_before(self):
        return self.job_before

    def get_job_after(self):
        return self.job_after

    # setters
    def set_job_before(self, job):
        self.job_before = job

    def set_job_after(self, job):
        self.job_after = job

