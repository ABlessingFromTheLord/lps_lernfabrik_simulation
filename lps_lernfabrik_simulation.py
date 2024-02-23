import math
import simpy
import numpy
import sqlite3
from Job import Job
from Order import Order
from OrderList import OrderList
from pymoo.core.problem import Problem
import numpy as np

# global variables
# breaking probability
BROKEN_ZEIT = 60
REPAIR_ZEIT = 60
MTTR = 2 * 60  # TODO: setting it to one minute causes terminated processes to be interrupted

# part names / working strings
OBERTEIL = "Oberteil"
UNTERTEIL = "Unterteil"
HALTETEIL = "Halteteil"
RING = "Ring"

# Unilokk definition
UNILOKK = [OBERTEIL, UNTERTEIL, HALTETEIL, RING]

# optimization parameters
OBERTEIL_PRODUCTION = 17
UNTERTEIL_PRODUCTION = 11
HALTETEIL_PRODUCTION = 49
RING_PRODUCTION = 97

OBERTEIL_ORDER = 0
UNTERTEIL_ORDER = 0
HALTETEIL_ORDER = 0
RING_ORDER = 0

# parts produced
OBERTEIL_COUNT = 0
UNTERTEIL_COUNT = 0
HALTETEIL_COUNT = 0
RING_COUNT = 0

ORDERS_FULFILLED = 0

# ruestungszeit
RUESTUNGS_ZEIT = 0

# unilokk created
UNILOKK_COUNT = 0


# global helper functions
def get_jobs_for_part(part_name):
    #  returns the jobs required to be done to create a certain part of Unilokk
    match part_name:
        case "Oberteil":
            return Oberteil_Jobs
        case "Unterteil":
            return Unterteil_Jobs
        case "Halteteil":
            return Halteteil_Jobs
        case "Ring":
            return Ring_Jobs


def increase_part_count(part_name, output):
    #  increase the respective part count after the machines for part by amount "output"
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT += output
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT += output
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT += output
        case "Ring":
            global RING_COUNT
            RING_COUNT += output


def decrease_part_count(part_name):
    #  decrease respective part count after a partis used for order fulfillment
    match part_name:
        case "Oberteil":
            global OBERTEIL_COUNT
            OBERTEIL_COUNT = OBERTEIL_COUNT - 1
        case "Unterteil":
            global UNTERTEIL_COUNT
            UNTERTEIL_COUNT = UNTERTEIL_COUNT - 1
        case "Halteteil":
            global HALTETEIL_COUNT
            HALTETEIL_COUNT = HALTETEIL_COUNT - 1
        case "Ring":
            global RING_COUNT
            RING_COUNT = RING_COUNT - 1


def get_mz(machine):
    # returns the Machinezuverlässigkeit for a machine while producing a certain part
    if machine == machine_jaespa:
        return 0.98
    elif machine == machine_gz200:
        return 0.85
    elif machine == machine_fz12:
        return 0.98
    elif machine == machine_arbeitsplatz_at_gz200 or machine == machine_arbeitsplatz_2:
        return 1


def get_cumulative_quality_grade(part_name):
    # ran after completion of the part creation process
    # returns cumulative quality grade of the machines used
    # i.e if quality grade is 98%, it means 98% of material produced are usable to the next stage
    # 2% are thrown away, to rectify this, we produce 102% of the order, hence multiply output
    # by cumulative quality grade
    match part_name:
        case "Oberteil":
            return 1 * 0.98 * 0.98 * 0.95
        case "Unterteil":
            return 1 * 0.98 * 0.98
        case "Halteteil":
            return 1 * 0.98 * 0.98
        case "Ring":
            return 1 * 0.98 * 1


def get_output_per_part(part_name):
    # returns amount of parts created from a 3000mm long rod of raw material
    match part_name:
        case "Oberteil":
            return 17
        case "Unterteil":
            return 11
        case "Halteteil":
            return 49
        case "Ring":
            return 97


def all_jobs_completed_for_part(part_name):
    # checks if the jobs necessary to complete  a certain part creation are done
    # when all jobs required for a certain part creation are done it returns true
    # resets all the booleans completed in jobs for the next round of part creation
    # if there are more of the same part to be created
    jobs_required = get_jobs_for_part(part_name)

    for job in jobs_required:
        if job.get_completed() == 0:
            return False

    for job in jobs_required:
        job.set_completed(job.get_completed() - 1)  # removing one job to combine to form a part
    print("completed jobs for ", part_name)
    return True


def insert_variable_into_table(table_name, ordered, produced, ruestungszeit):
    # inserts statistics into out sqlite database
    sqlite_connection = sqlite3.connect('statistics.db')
    try:
        cursor = sqlite_connection.cursor()
        print("Connected to SQLite")

        sqlite_insert_with_param = f"""INSERT INTO {table_name}
                          (ordered, produced, ruestungszeit) 
                          VALUES (?, ?, ?);"""

        data_tuple = (ordered, produced, ruestungszeit)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        sqlite_connection.commit()
        print("Python Variables inserted successfully into SqliteDb_developers table")

        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert Python variable into sqlite table", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("The SQLite connection is closed")


def amount_of_runs(order_list):
    # returns amount of runs needed to fulfill the order
    # it depends on how much order is left and how much is needed
    # at the beginning nothing is produced so nothing is left

    global OBERTEIL_COUNT
    global UNTERTEIL_COUNT
    global HALTETEIL_COUNT
    global RING_COUNT

    # showing remaining parts from previous execution
    print("\nOBERTEIL: ", OBERTEIL_COUNT)
    print("UNTERTEIL: ", UNTERTEIL_COUNT)
    print("HALTETEIL: ", HALTETEIL_COUNT)
    print("RING: ", RING_COUNT, "\n")

    # if we are just starting
    if OBERTEIL_COUNT == 0 and UNTERTEIL_COUNT == 0 and HALTETEIL_COUNT == 0 and RING_COUNT == 0:
        for order_instance in range(len(order_list)):
            if order_list[order_instance] == 0:
                order_list[order_instance] = 0
            else:
                match order_instance:
                    case 0:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 17)
                    case 1:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 11)
                    case 2:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 49)
                    case 3:
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 97)

    # we already produced and have some leftovers
    else:
        # if the leftovers suffice, done produce more
        if OBERTEIL_COUNT > order_list[0]:
            order_list[0] = 0
        if UNTERTEIL_COUNT > order_list[1]:
            order_list[1] = 0
        if HALTETEIL_COUNT > order_list[2]:
            order_list[2] = 0
        if RING_COUNT > order_list[3]:
            order_list[3] = 0

        # else produce needed
        # to reduce order by what is available
        for order_instance in range(len(order_list)):
            if order_list[order_instance] > 0:
                match order_instance:
                    case 0:
                        order_list[order_instance] -= OBERTEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 17)
                    case 1:
                        order_list[order_instance] -= UNTERTEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 11)
                    case 2:
                        order_list[order_instance] -= HALTETEIL_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 49)
                    case 3:
                        order_list[order_instance] -= RING_COUNT
                        order_list[order_instance] = math.ceil(order_list[order_instance] / 97)

    return order_list


def get_degree(job):
    # returns degree of a job
    # TODO: explain what a degree is
    return job.get_degree()


def get_parts_by_sequence(sequence):
    # returns part names in the amount their machines are needed to be executed
    # to get a batch that can fulfill an order
    to_return = []

    for j in range(len(sequence)):
        match j:
            case 0:
                while sequence[j] > 0:
                    to_return.append("Oberteil")
                    sequence[j] -= 1
            case 1:
                while sequence[j] > 0:
                    to_return.append("Unterteil")
                    sequence[j] -= 1
            case 2:
                while sequence[j] > 0:
                    to_return.append("Halteteil")
                    sequence[j] -= 1
            case 3:
                while sequence[j] > 0:
                    to_return.append("Ring")
                    sequence[j] -= 1
    return to_return


def get_job_keys(job):
    # returns a custom assigned key to a job to help in sorting process before
    # batching jobs together to minimize Ruestungszeit
    match job.get_name():
        case "Oberteil_Saegen":
            return 1
        case "Oberteil_Drehen":
            return 2
        case "Oberteil_Fraesen":
            return 3
        case "Unterteil_Saegen":
            return 4
        case "Unterteil_Drehen":
            return 5
        case "Halteteil_Saegen":
            return 6
        case "Halteteil_Drehen":
            return 7
        case "Ring_Saegen":
            return 8
        case "Ring_Drehen":
            return 9
        case "Ring_Senken":
            return 10


def get_job_with_minimal_degree(job_list):
    # returns the job with the minimal degree, ie, the job that should be executed first
    job_with_minimal_degree = None

    for i in range(len(job_list)):
        if i == 0:
            job_with_minimal_degree = job_list[i]
        else:
            if job_list[i].get_degree() < job_with_minimal_degree.get_degree():
                job_with_minimal_degree = job_list[i]

    return job_with_minimal_degree


def get_job_with_minimal_degree_by_part(part_name, done_jobs, jobs_to_be_done, drehen_sequence, job_list):
    # returns the job with the minimal degree, ie, the job that should be executed first
    # this should also take into account that the machine needed to run this job is free
    jobs_copy = [x for x in job_list if x.get_part_name() == part_name]
    job_with_minimal_degree = None

    # machine for part is already added, no need to look for another job
    for job in jobs_to_be_done:
        if job.get_part_name() == part_name:
            return None

    # just starting, no done jobs. getting jobs before can be disregarded
    if len(done_jobs) == 0:
        job_with_minimal_degree = jobs_copy[0]

        for job in jobs_copy:
            if job.get_degree() < job_with_minimal_degree.get_degree():
                job_with_minimal_degree = job
        return job_with_minimal_degree

    # some jobs have already been done, but there is no corresponding job for part
    if len(jobs_copy) == 0:
        index_for_old_part = drehen_sequence.index(part_name)

        if index_for_old_part + 1 >= len(drehen_sequence):
            return None

        new_part = drehen_sequence[index_for_old_part + 1]

        if new_part == part_name:
            return None

        new_jobs = [x for x in job_list if x.get_part_name() == new_part]
        return get_job_with_minimal_degree(new_jobs)

    # some jobs have been done and there is one for part
    if jobs_copy[0].get_job_before() is not None:
        if jobs_copy[0].get_machine_required().count < jobs_copy[0].get_machine_required().capacity \
                and jobs_copy[0].get_job_before().get_completed() >= 1:
            job_with_minimal_degree = jobs_copy[0]
    else:
        if jobs_copy[0].get_machine_required().count < jobs_copy[0].get_machine_required().capacity:
            job_with_minimal_degree = jobs_copy[0]

    # none was found since no proceeding job is in done jobs
    if job_with_minimal_degree is None:
        for job in jobs_copy:
            if job.get_machine_required().count < job.get_machine_required().capacity:
                job_with_minimal_degree = job
                break

    # Machines for all parts are busy
    if job_with_minimal_degree is None:
        return None

    # at least one part has machines free and looking for job with minimal degree is possible
    for i in range(1, len(jobs_copy)):
        if (jobs_copy[i].get_degree() < job_with_minimal_degree.get_degree()
            and jobs_copy[i].get_job_before() in done_jobs) \
                and jobs_copy[i].get_machine_required().count < jobs_copy[i].get_machine_required().capacity:
            job_with_minimal_degree = jobs_copy[i]

    return job_with_minimal_degree


def get_job_with_degree(job_list, degree):
    # returns the job with the specified degree, if not found it returns None
    job_to_return = None

    for job in job_list:
        if job.get_degree() == degree:
            job_to_return = job
            break

    return job_to_return


def check_machine_availability(jobs_to_be_done, job):
    # checks if the job to be done does not coincide with another job that needs the same machinery
    # this is before execution

    for i in jobs_to_be_done:
        if i.get_machine_required() == job.get_machine_required():
            return False

    return True


def get_equipping_time(job_1, job_2):
    # returns the equipping time of the job about to be executed
    # if the job is a Drehjob, ie, a job that needs machine gz200
    # then argument job_1 is relevant, otherwise it is irrelevant although passed as argument

    if job_2.get_machine_required() == machine_gz200:
        if job_1 is None:
            return 0

        match job_1.get_name():
            case "Oberteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 0
                    case "Unterteil_Drehen":
                        return 45 * 60
                    case "Halteteil_Drehen":
                        return 40 * 60
                    case "Ring_Drehen":
                        return 45 * 60

            case "Unterteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 45 * 60
                    case "Unterteil_Drehen":
                        return 0
                    case "Halteteil_Drehen":
                        return 40 * 60
                    case "Ring_Drehen":
                        return 45 * 60

            case "Halteteil_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 40 * 60
                    case "Unterteil_Drehen":
                        return 40 * 60
                    case "Halteteil_Drehen":
                        return 0
                    case "Ring_Drehen":
                        return 45 * 60

            case "Ring_Drehen":
                match job_2.get_name():
                    case "Oberteil_Drehen":
                        return 45 * 60
                    case "Unterteil_Drehen":
                        return 45 * 60
                    case "Halteteil_Drehen":
                        return 45 * 60
                    case "Ring_Drehen":
                        return 0

    elif job_2.get_machine_required() == machine_fz12:
        return 30 * 60
    elif job_2.get_machine_required() == machine_jaespa:
        return 0
    elif ((job_2.get_machine_required() == machine_arbeitsplatz_at_gz200)
          or (job_2.get_machine_required() == machine_arbeitsplatz_2)):
        return 0


def get_next_job_with_minimal_runtime(job, job_list):
    # returns the next Drehjob that should be run after this one to get minimal equipping times
    next_job = job_list[0]
    min_runtime = get_equipping_time(job, job_list[0])

    for i in range(1, len(job_list)):
        if get_equipping_time(job, job_list[i]) < min_runtime:
            min_runtime = get_equipping_time(job, job_list[i])
            next_job = job_list[i]

    return next_job


def sort_drehjobs_by_minimal_runtime(previous_drehen, job_list):
    # return the job execution sequence of the Drehjobs with minimal Ruestungszeit
    if len(job_list) <= 1:
        return job_list

    min_run = []

    # execution is just starting out
    if previous_drehen is None:
        if Oberteil_Drehen in job_list:
            job_with_minimal_degree = Oberteil_Drehen
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)
        else:
            job_with_minimal_degree = get_job_with_minimal_duration(job_list)
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)

    else:
        # there was a previous execution, hence that is used as our first job only
        # if it is in the list
        if previous_drehen in job_list:
            job_with_minimal_degree = previous_drehen
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)
        # previous drehen not none but it is not in the list
        else:
            job_with_minimal_degree = get_next_job_with_minimal_runtime(previous_drehen, job_list)
            min_run.append(job_with_minimal_degree)
            job_list.remove(job_with_minimal_degree)

    job_index = 0
    n = len(job_list)

    while job_index < n:
        job_with_min_runtime = get_next_job_with_minimal_runtime(min_run[-1], job_list)
        min_run.append(job_with_min_runtime)
        job_list.remove(job_with_min_runtime)
        job_index += 1

    return min_run


def get_job_with_minimal_duration(job_list):
    # returns the next job with the shortest duration or runtime
    next_job = job_list[0]

    for i in range(len(job_list)):
        if job_list[i].get_duration() < next_job.get_duration():
            next_job = job_list[i]

    return next_job


def get_runnable_jobs(done_jobs, jobs_list):
    # returns a lost of jobs that are eligible to be run
    to_return = []

    for job in jobs_list:
        if job.get_machine_required().count < job.get_machine_required().capacity:
            if job.get_job_before() is None:
                to_return.append(job)
            else:
                if job.get_job_before().get_completed() >= 1:
                    to_return.append(job)

    return to_return


def get_depth(job_list):
    # depth is defined as the amount of machines that can be run at the same time
    # in contrast to degree which is the stage of a job in the sequence of execution
    depth = 0

    machines = []

    for job in job_list:
        if job.get_machine_required() not in machines:
            machines.append(job.get_machine_required())
            depth += 1

    return depth


def get_parallelization_1(jobs):
    # returns an array of arrays that indicate the jobs that can be executed in parallel
    # jobs in the same inner array need the same machine to be done, so they cannot be
    # parallelized. Only jobs in different inner arrays can be run consequently

    parallel_jobs = []
    temp = []
    n = len(jobs)

    job_index_1 = 0
    while job_index_1 < n:
        job_1 = jobs[job_index_1]
        machine = job_1.get_machine_required()
        if job_1 not in temp:
            temp.append(job_1)
            jobs.remove(job_1)
            n -= 1

            job_2_index = 0
            while job_2_index < n:
                if jobs[job_2_index].get_machine_required() == machine:
                    temp.append(jobs[job_2_index])
                    jobs.remove(jobs[job_2_index])
                    n -= 1
                else:
                    job_2_index += 1
            parallel_jobs.append(temp.copy())
            temp.clear()
        else:
            job_index_1 += 1

    return parallel_jobs


def get_next_jobs(jobs_list):
    next_jobs = []

    for job in jobs_list:
        if (job.get_completed() >= 1 and job.get_job_after()
                and job.get_machine_required().count < job.get_machine_required().capacity):
            next_jobs.append(job.get_job_after())

    return next_jobs


def get_jobs_in_parallel(bands, previously_done_jobs, jobs_list):
    # returns jobs that can be run in parallel
    # TODO: define bands
    parallel_jobs = []

    if bands == 1:
        parallel_jobs.append(get_job_with_minimal_duration(jobs_list))
        return parallel_jobs  # here only one job will be in jobs
    else:
        parallel_jobs.extend(get_next_jobs(previously_done_jobs))
        parallel_jobs.append(get_job_with_minimal_degree(jobs_list))
        return parallel_jobs


def submit_orders(order):
    # receives orders and sets the universal variables OBERTEIL_ORDER,
    # UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER
    global OBERTEIL_ORDER
    OBERTEIL_ORDER = order
    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = order
    global HALTETEIL_ORDER
    HALTETEIL_ORDER = order
    global RING_ORDER
    RING_ORDER = order


def get_parts_needed(order):
    # receives orders and sets the universal variables OBERTEIL_ORDER,
    # UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER

    global OBERTEIL_ORDER
    OBERTEIL_ORDER = order
    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = order
    global HALTETEIL_ORDER
    HALTETEIL_ORDER = order
    global RING_ORDER
    RING_ORDER = order

    return [OBERTEIL_ORDER, UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER]


def clear_stats():
    global OBERTEIL_COUNT
    OBERTEIL_COUNT = 0
    global UNTERTEIL_COUNT
    UNTERTEIL_COUNT = 0
    global HALTETEIL_COUNT
    HALTETEIL_COUNT = 0
    global RING_COUNT
    RING_COUNT = 0

    global UNILOKK_COUNT
    UNILOKK_COUNT = 0
    global RUESTUNGS_ZEIT
    RUESTUNGS_ZEIT = 0


def adjust(genes):
    # if the machine capacity greater than order, genes are always zero
    # this method adjusts that to make sure if that's the case, then the
    # machine is run at least once
    # other use case of the method is to round up
    copy = []
    for k in range(len(genes)):
        if 0 < genes[k] < 1:
            genes[k] = 1
            copy.append(int(genes[k]))
        else:
            genes[k] = math.ceil(genes[k])
            copy.append(int(genes[k]))
    return copy


def fill_with_zeroes(array, n):
    # returns an array appended with zeroes to the length n
    # useful so all arrays have same dimension later in optimization algorithm
    while len(array) < n:
        array.append(0)
    return array


# optimization
# submit order

# submit order and run algorithm
# submit_order([1, 3, 4, 2, 6, 1])  # each index is a customer number


# optimization problem definition
class ExecutionAmounts(Problem):
    def __init__(self):
        super().__init__(n_var=4, n_obj=1, n_constr=0, xl=np.array([0, 0, 0, 0]),
                         xu=np.array([OBERTEIL_ORDER, UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER]))

    def _evaluate(self, x, out, *args, **kwargs):
        total_oberteil = np.zeros(len(x))
        total_unterteil = np.zeros(len(x))
        total_halteteil = np.zeros(len(x))
        total_ring = np.zeros(len(x))

        for m in range(len(x)):
            if OBERTEIL_COUNT == 0 and x[m, 0] == 0:
                total_oberteil[m] = 1
            elif x[m, 0] > 0:
                total_oberteil[m] = OBERTEIL_PRODUCTION * x[m, 0]

            if UNTERTEIL_COUNT == 0 and x[m, 1] == 0:
                total_oberteil[m] = 1
            elif x[m, 1] > 0:
                total_unterteil[m] = UNTERTEIL_PRODUCTION * x[m, 1]

            if HALTETEIL_COUNT == 0 and x[m, 2] == 0:
                total_halteteil[m] = 1
            elif x[m, 2] > 0:
                total_halteteil[m] = HALTETEIL_PRODUCTION * x[m, 2]

            if RING_COUNT == 0 and x[m, 3] == 0:
                total_ring[m] = 1
            elif x[m, 3] > 0:
                total_ring[m] = RING_PRODUCTION * x[m, 3]

        fitness = (np.abs(total_oberteil - OBERTEIL_ORDER) + np.abs(total_unterteil - UNTERTEIL_ORDER) +
                   np.abs(total_halteteil - HALTETEIL_ORDER) + np.abs(total_ring - RING_ORDER))

        out["F"] = fitness[:, None]  # Reshape to match the expected shape
        out["G"] = np.zeros((len(x), 0))  # No constraints for now


# simulation class
class Lernfabrik:
    # this class simulates all processes taking place in the factory
    def __init__(self, sim_env):
        self.process = None
        self.env = sim_env  # environment variable
        self.currently_broken = False  # boolean for denoting when a machine is broken
        self.previously_created = ""  # string to denote the previously created part
        self.next_creating = ""  # string to denote the next created part
        self.previous_drehen_job = None
        self.done_once = False  # if true means the machine GZ200 in Ring creation has already been operated once
        self.orders = OrderList()  # custom data type to receive orders, initially Null
        self.done_jobs = []

    # operation
    def operation(self, machine, operating_time, job_name):
        #  simulates an operation, it is an abstract function

        # operating machine after equipping
        while operating_time:
            start = self.env.now
            try:
                print(f"execution time of {job_name} is {operating_time} seconds, started execution at {self.env.now}")
                yield self.env.timeout(operating_time)  # running operation
                self.process = None
                operating_time = 0
                print(f"finish time is {self.env.now} seconds")

            except simpy.Interrupt:
                self.currently_broken = True

                print(f"Machine{machine} got PREEMPTED at {self.env.now}")  # TODO: comment out after proving
                operating_time -= (self.env.now - start)  # remaining time from when breakdown occurred

                # producing random repair time in the gaussian distribution with mean 60 seconds and standard
                # deviation of 30 seconds
                repair_time = abs(numpy.floor(numpy.random.normal(60, 30, 1).item()).astype(int).item())
                yield self.env.timeout(repair_time)
                print(f"remaining time for operation {operating_time} seconds, continues at {self.env.now}")

                self.currently_broken = False

    # Helper functions
    def break_machine(self, machine, priority, preempt):
        #  breaks down a certain machine based on it's break probability or Maschinenzuverlässigkeit
        while True:
            break_or_not = numpy.around(numpy.random.uniform(0, 1), 2) < (1 - get_mz(machine))
            yield self.env.timeout(MTTR)  # Time between two successive machine breakdowns

            # if true then machine breaks down, else continues running
            if break_or_not:
                with machine.request(priority=priority, preempt=preempt) as request:
                    assert isinstance(self.env.now, int), type(self.env.now)
                    yield request
                    assert isinstance(self.env.now, int), type(self.env.now)

                    if self.process is not None and not self.currently_broken:
                        self.process.interrupt()

    def do_job(self, job):
        # performs a certain job as subprocess in part creation process
        # input amount is passed to diminish it based on machine's Qualitätsgrad after this job is done
        required_machine = job.get_machine_required()
        equipping_time = get_equipping_time(self.previous_drehen_job, job)
        operating_time = job.get_duration()

        if job.get_machine_required() == machine_gz200 and self.previous_drehen_job is not None:
            print("\n")
            print("Ruestungszeit from ", self.previous_drehen_job.get_name(), " to ", job.get_name(), " is ", equipping_time)
            print("\n")

        global RUESTUNGS_ZEIT
        RUESTUNGS_ZEIT += equipping_time  # collect Ruestungszeit for statistical purposes#

        if required_machine == machine_gz200:
            self.previous_drehen_job = job  # storing what job came to calculate the Ruestungszeit

        with required_machine.request(priority=1, preempt=False) as request:
            yield request
            yield self.env.timeout(equipping_time)
            self.process = self.env.process(self.operation(
                required_machine, operating_time, job.get_name()))  # operating machinery
            self.env.process(self.break_machine(required_machine, 2, True))  # starting breakdown function
            yield self.process

            self.process = None

    def series_job_execution(self, jobs_in_series):
        # called n times to execute the rest of the jobs that cannot be parallelized
        # its execution is in series
        for job in jobs_in_series:
            part_name = job.get_part_name()
            amount_produced = get_output_per_part(part_name)

            yield self.env.process(self.do_job(job))

            job.set_completed(job.get_completed() + 1)  # incrementing times the job is done
            self.done_jobs.append(job)

            if all_jobs_completed_for_part(part_name):
                #  all machines required to produce a part have been operated part is created
                total_defected_parts = 1 - get_cumulative_quality_grade(part_name)

                # to compensate for the defected parts due to machine's quality grade,
                # we produce (100% of order + cumulative quality grade)
                amount_produced *= (1 + total_defected_parts)
                increase_part_count(part_name, math.floor(amount_produced))  # add newly created part

                print(math.floor(amount_produced), part_name, "(s) was created at ", self.env.now, "\n")

    def parallel_job_execution(self, jobs_in_parallel):
        # called n times as our parallelized_jobs array to execute jobs in parallel
        for job in jobs_in_parallel:
            self.env.process(self.series_job_execution([job]))
            yield self.env.timeout(0)

    def fulfill_with_parallelization(self, order_number, order):
        # received and order and fulfills it
        global UNILOKK_COUNT
        remaining_unilokk = UNILOKK_COUNT
        UNILOKK_COUNT = 0

        if order is None:
            return

        # need to produce if our order exceeds what is available
        if order.amount > remaining_unilokk:
            working_order = order.amount - remaining_unilokk  # actual order needed to be produced

            print("leftover Unilokk ", remaining_unilokk)

            parts_needed = get_parts_needed(working_order)
            print(parts_needed)

            execution_sequence = amount_of_runs(parts_needed)
            print("execution sequence", execution_sequence)
            execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
            print("execution sequence by parts", execution_sequence_in_parts)

            # parts creation
            jobs = []  # array of jobs needed to fulfill this order

            for part in execution_sequence_in_parts:
                jobs_for_part = get_jobs_for_part(part)

                # unpacking jobs into one list full of all the jobs
                for job in jobs_for_part:
                    jobs.append(job)

            print("\nBefore degree sort:")
            for job in jobs:
                print(job.get_name())
            print("\n")

            amount_of_jobs_to_be_done = len(jobs)

            # getting the minimal order for the Drehjobs
            drehen_jobs = [x for x in jobs if x.get_machine_required() == machine_gz200]
            other_jobs = [x for x in jobs if x.get_machine_required() != machine_gz200]
            drehen_jobs = sort_drehjobs_by_minimal_runtime(self.previous_drehen_job, drehen_jobs)

            drehen_sequence = []
            for job in drehen_jobs:
                drehen_sequence.append(job.get_part_name())

            # add jobs in jobs array in the right order in which Drehen jobs are to be executed
            jobs.clear()
            jobs.extend(other_jobs)

            print("\norder of Drehen jobs:")
            for job in drehen_jobs:
                print(job.get_name())
            print("\n")

            depth = get_depth(jobs)
            previously_done_jobs = []
            iteration = 0
            current_dreh_job = 0

            while len(self.done_jobs) < amount_of_jobs_to_be_done:
                # we are only starting out
                if iteration == 0:
                    first_job = get_job_with_minimal_degree_by_part(
                        drehen_jobs[current_dreh_job].get_part_name(), self.done_jobs, [], drehen_sequence, jobs)
                    yield self.env.process(self.series_job_execution([first_job]))
                    previously_done_jobs.append(first_job)
                    jobs.remove(first_job)
                    iteration += 1
                    current_dreh_job += 1

                else:
                    current_depth = 0
                    to_do = []

                    # check if the machine GZ200 is free, if yes run the next drehen job
                    if machine_gz200.count < machine_gz200.capacity and len(drehen_jobs) > 0:
                        to_do.append(drehen_jobs[0])
                        drehen_jobs.remove(drehen_jobs[0])
                        current_depth += 1

                    # if there is a job that is ready to run
                    nj = get_runnable_jobs(self.done_jobs, jobs)
                    if len(nj) > 0:
                        for job in nj:
                            if (job not in to_do and current_depth < depth
                                    and check_machine_availability(to_do, job)):
                                to_do.append(job)
                                jobs.remove(job)
                                current_depth += 1

                    # find the next runnable job with minimal degree whose resource is free
                    if iteration >= len(drehen_sequence):
                        iteration = 1

                    if len(drehen_sequence) == 1:
                        iteration = 0

                    next_job = None
                    if len(drehen_jobs) > 0:
                        last_drehen = drehen_jobs[0].get_part_name()
                        index_drehen = drehen_sequence.index(last_drehen)

                        next_job = get_job_with_minimal_degree_by_part(
                            drehen_sequence[index_drehen], self.done_jobs, to_do, drehen_sequence, jobs)

                    if next_job is not None and next_job not in to_do and current_depth < depth \
                            and next_job.get_machine_required().count < next_job.get_machine_required().capacity:
                        to_do.append(next_job)
                        jobs.remove(next_job)
                        current_depth += 1

                    # out of while loop
                    # do the jobs in parallel
                    if len(to_do) > 0:
                        yield self.env.process(self.parallel_job_execution(to_do))

                        previously_done_jobs.clear()
                        previously_done_jobs.extend(to_do)
                        iteration += 1

                    else:
                        yield self.env.timeout(1)
                        iteration += 1

        # else we already have enough to fulfill order, or we have produced enough
        # assembling parts
        yield self.env.process(self.finish_unilokk_creation())

        print("\nOrder", order_number, ":", order.amount, " , produced:", UNILOKK_COUNT,
              ", remaining:", remaining_unilokk, ", total:", remaining_unilokk + UNILOKK_COUNT)

        # fulfilling order
        if UNILOKK_COUNT >= (order.amount - remaining_unilokk):
            UNILOKK_COUNT -= (order.amount - remaining_unilokk)
            global ORDERS_FULFILLED
            ORDERS_FULFILLED += 1

            self.done_jobs.clear()

            print("Order fulfilled completely\n\n")
        else:
            self.done_jobs.clear()

            print("Order unfulfilled\n\n")

    def fulfill_order_with_opt(self, order_number, order):
        # received and order and fulfills it
        # before this method Ruestungszeit was 19800 (running all jobs in jobs list)
        global UNILOKK_COUNT
        remaining_unilokk = UNILOKK_COUNT
        UNILOKK_COUNT = 0

        # need to produce if our order exceeds what is available
        if order.amount > remaining_unilokk:
            working_order = order.amount - remaining_unilokk  # actual order needed to be produced

            print("leftover Unilokk ", remaining_unilokk)

            parts_needed = get_parts_needed(working_order)
            print(parts_needed)

            execution_sequence = amount_of_runs(parts_needed)
            print("execution sequence", execution_sequence)
            execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
            print("execution sequence by parts", execution_sequence_in_parts)

            # parts creation
            jobs = []  # array of jobs needed to fulfill this order

            for part in execution_sequence_in_parts:
                jobs_for_part = get_jobs_for_part(part)

                # unpacking jobs into one list full of all the jobs
                for job in jobs_for_part:
                    jobs.append(job)

            print("\n Jobs before Drehjobs min runtime:")
            for job in jobs:
                print(job.get_name())
            print("\n")

            # ordering the drehjobs in the order of minimal Ruestungszeit
            # we do not care about other jobs since they have constant Ruestungszeit
            drehen_jobs = [x for x in jobs if x.get_machine_required() == machine_gz200]
            drehen_jobs = sort_drehjobs_by_minimal_runtime(drehen_jobs)

            print("\nDrehjobs with minimal runtime:")
            for job in drehen_jobs:
                print(job.get_name())
            print("\n")

            # append jobs according to degree
            saegen_jobs = [x for x in jobs if x.get_machine_required() == machine_jaespa]
            fraesen_jobs = [x for x in jobs if x.get_machine_required() == machine_fz12]
            senken_jobs = [x for x in jobs if x.get_machine_required() == machine_arbeitsplatz_at_gz200]

            jobs_to_run = []
            jobs_to_run.extend(saegen_jobs)
            jobs_to_run.extend(drehen_jobs)
            jobs_to_run.extend(fraesen_jobs)
            jobs_to_run.extend(senken_jobs)

            # order or jobs for minimal Ruestungszeiten
            for job in jobs_to_run:
                # check if job required to be done before this is done
                if job.get_job_before() is not None and job.get_job_before().get_completed() <= 0:
                    print(job.get_job_before().get_name(), " has to be done before ", job.get_name())
                    jobs_to_run.insert(jobs_to_run.index(job.get_job_before()) + 1,
                                       job)  # inserting job after its prerequisite
                else:
                    part_name = job.get_part_name()
                    amount_produced = get_output_per_part(part_name)
                    yield self.env.process(self.do_job(job))

                    job.set_completed(job.get_completed() + 1)  # incrementing times the job is done

                    if all_jobs_completed_for_part(part_name):
                        #  all machines required to produce a part have been operated part is created
                        total_defected_parts = 1 - get_cumulative_quality_grade(part_name)

                        # to compensate for the defected parts due to machine's quality grade,
                        # we produce (100% of order + cumulative quality grade)
                        amount_produced *= (1 + total_defected_parts)
                        increase_part_count(part_name, math.floor(amount_produced))  # add newly created part

                        print(math.floor(amount_produced), part_name, "(s) was created at ", self.env.now, "\n")

        # assembling parts
        yield self.env.process(self.finish_unilokk_creation())

        print("\nOrder", order_number, ":", order.amount, " , produced:", UNILOKK_COUNT,
              ", remaining:", remaining_unilokk, ", total:", remaining_unilokk + UNILOKK_COUNT)

        # fulfilling
        # hint: (order.amount - remaining_unilokk) is same as working_order from up there
        if UNILOKK_COUNT >= (order.amount - remaining_unilokk):
            UNILOKK_COUNT -= (order.amount - remaining_unilokk)
            global ORDERS_FULFILLED
            ORDERS_FULFILLED += 1

            self.done_jobs.clear()

            print("Order fulfilled completely\n")

            print("Remaining parts ")
            print("OBERTEIL ", OBERTEIL_COUNT)
            print("UNTERTEIL ", UNTERTEIL_COUNT)
            print("HALTETEIL ", HALTETEIL_COUNT)
            print("RING ", RING_COUNT)
            print("\n")
            # printing remaining parts

        else:
            self.done_jobs.clear()

            print("Order unfulfilled\n\n")

    def finish_unilokk_creation(self):
        # simulates the Kleben, Montage, Pruefen and Verpacken processes
        # after parts have been created
        print("\nFinishing process has started")

        n = 1
        # then assemble them into Unilokk
        while True:
            if OBERTEIL_COUNT > 0 and UNTERTEIL_COUNT > 0 and HALTETEIL_COUNT > 0 and RING_COUNT > 0:
                yield self.env.process(self.operation(machine_arbeitsplatz_2, 180, "finishing process"))

                # decrement for the parts used above to create a whole Unilokk
                decrease_part_count(OBERTEIL)
                decrease_part_count(UNTERTEIL)
                decrease_part_count(HALTETEIL)
                decrease_part_count(RING)

                # increase Unilokk count for the one that is created
                global UNILOKK_COUNT
                UNILOKK_COUNT = UNILOKK_COUNT + 1

                print("unilokk ", n, " was created at ", self.env.now, "\n")
                n = n + 1

            else:
                break

    def fulfill_orders(self, orders_list):
        # the whole process from part creation to order fulfillment

        # receiving and prioritising orders
        self.orders.receive_order(orders_list)
        prioritized_list = self.orders.order_by_priority()

        for order_number in range(len(prioritized_list)):
            yield self.env.process(self.fulfill_with_parallelization(
                order_number + 1, prioritized_list[order_number]))

        print("\nOrders fulfilled:", ORDERS_FULFILLED, "/", len(prioritized_list))


# instantiate object of Lernfabrik class
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.PreemptiveResource(env, capacity=1)  # Maschine zum Saegen
machine_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Drehen
machine_fz12 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Fräsen
machine_arbeitsplatz_at_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage

# machines for part creation
OBERTEIL_MACHINES = [machine_jaespa, machine_gz200, machine_fz12]
UNTERTEIL_MACHINES = [machine_jaespa, machine_gz200]
HALTETEIL_MACHINES = [machine_jaespa, machine_gz200]
RING_MACHINES = [machine_jaespa, machine_gz200, machine_arbeitsplatz_at_gz200]

# instantiating jobs
# Oberteil creation jobs
Oberteil_Saegen = Job("Oberteil_Saegen", "Oberteil", 34, machine_jaespa)
Oberteil_Drehen = Job("Oberteil_Drehen", "Oberteil", 287, machine_gz200)
Oberteil_Fraesen = Job("Oberteil_Fraesen", "Oberteil", 376, machine_fz12)
Oberteil_Saegen.set_job_before(None)
Oberteil_Saegen.set_job_after(Oberteil_Drehen)
Oberteil_Saegen.set_degree(0)
Oberteil_Drehen.set_job_before(Oberteil_Saegen)
Oberteil_Drehen.set_job_after(Oberteil_Fraesen)
Oberteil_Drehen.set_degree(1)
Oberteil_Fraesen.set_job_before(Oberteil_Drehen)
Oberteil_Fraesen.set_job_after(None)
Oberteil_Fraesen.set_degree(2)
Oberteil_Jobs = [Oberteil_Saegen, Oberteil_Drehen, Oberteil_Fraesen]

# Unterteil creation jobs
Unterteil_Saegen = Job("Unterteil_Saegen", "Unterteil", 20, machine_jaespa)
Unterteil_Drehen = Job("Unterteil_Drehen", "Unterteil", 247, machine_gz200)
Unterteil_Saegen.set_job_before(None)
Unterteil_Saegen.set_job_after(Unterteil_Drehen)
Unterteil_Saegen.set_degree(0)
Unterteil_Drehen.set_job_before(Unterteil_Saegen)
Unterteil_Drehen.set_job_after(None)
Unterteil_Drehen.set_degree(1)
Unterteil_Jobs = [Unterteil_Saegen, Unterteil_Drehen]

# Halteteil creation jobs
Halteteil_Saegen = Job("Halteteil_Saegen", "Halteteil", 4, machine_jaespa)
Halteteil_Drehen = Job("Halteteil_Drehen", "Halteteil", 255, machine_gz200)
Halteteil_Saegen.set_job_before(None)
Halteteil_Saegen.set_job_after(Halteteil_Drehen)
Halteteil_Saegen.set_degree(0)
Halteteil_Drehen.set_job_before(Halteteil_Saegen)
Halteteil_Drehen.set_job_after(None)
Halteteil_Drehen.set_degree(1)
Halteteil_Jobs = [Halteteil_Saegen, Halteteil_Drehen]

# Ring creation jobs
Ring_Saegen = Job("Ring_Saegen", "Ring", 3, machine_jaespa)
Ring_Drehen = Job("Ring_Drehen", "Ring", 185, machine_gz200)
Ring_Senken = Job("Ring_Senken", "Ring", 20, machine_arbeitsplatz_at_gz200)
Ring_Saegen.set_job_before(None)
Ring_Saegen.set_job_after(Ring_Drehen)
Ring_Saegen.set_degree(0)
Ring_Drehen.set_job_before(Ring_Saegen)
Ring_Drehen.set_job_after(Ring_Senken)
Ring_Drehen.set_degree(1)
Ring_Senken.set_job_before(Ring_Drehen)
Ring_Senken.set_job_after(None)
Ring_Senken.set_degree(2)
Ring_Jobs = [Ring_Saegen, Ring_Drehen, Ring_Senken]

# Finishing jobs
Fertigstellung = Job("Kleben_Montage_Pruefen_Verpacken", "Not_Applicable", 180, machine_arbeitsplatz_2)
Fertigstellung.set_job_before(None)
Fertigstellung.set_job_after(None)
Finishing_Jobs = [Fertigstellung]

SIM_TIME = 86400
fabric = Lernfabrik(env)

# creating order and add them to order list
# orders could also be created randomly, so random amount and random priority
order_1 = Order(5, 2)
order_2 = Order(20, 15)
order_3 = Order(15, 20)
order_4 = Order(35, 27)
order_5 = Order(10, 3)
order_6 = Order(15, 38)
order_7 = Order(30, 45)
order_8 = Order(25, 10)
order_9 = Order(20, 55)
order_10 = Order(25, 65)

orders = [order_1, order_2, order_3, order_4, order_5, order_6, order_7, order_8, order_9, order_10]
#orders = [order_4]
env.process(fabric.fulfill_orders(orders))
env.run(until=2*SIM_TIME)

# analysis and results
print("\ntotal ruestungszeit: ", RUESTUNGS_ZEIT, "\n")
