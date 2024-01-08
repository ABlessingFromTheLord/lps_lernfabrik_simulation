import simpy as sp

class Machine:
    def __init__(self, env,name, broken_time):
        self.env = env
        self.name = name
        self.broken = False
        self.broken_time = broken_time

    def break_machine(self):
        while True:
            yield self.env.timeout(self.broken_time)
            if not self.broken:
                # only break when currently working
                self.process.interrupt()