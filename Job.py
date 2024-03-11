class Job:
    # definition of how a job made in the simulation looks like
    def __init__(self, name, part_name, duration, machine, machine_codename):
        self.__name = name
        self.__part_name = part_name
        self.__duration = duration
        self.__job_before = Job
        self.__job_after = Job
        self.__machine_required = machine
        self.__machine_codename = machine_codename
        self.__completed = 0
        self.__depth = None
        self.__amount_produced = 0

    # getters
    def get_name(self):
        return self.__name

    def get_part_name(self):
        return self.__part_name

    def get_duration(self):
        return self.__duration

    def get_job_before(self):
        return self.__job_before

    def get_job_after(self):
        return self.__job_after

    def get_machine_required(self):
        return self.__machine_required

    def get_machine_codename(self):
        return self.__machine_codename

    def get_completed(self):
        return self.__completed

    def get_depth(self):
        return self.__depth

    def get_amount_produced(self):
        return self.__amount_produced

    # setters
    def set_job_before(self, job):
        self.__job_before = job

    def set_job_after(self, job):
        self.__job_after = job

    def set_completed(self, value):
        self.__completed = value

    def set_depth(self, value):
        self.__depth = value

    def set_amount_produced(self, value):
        self.__amount_produced = value
