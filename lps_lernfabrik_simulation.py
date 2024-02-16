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
PARTS_MADE = 0

# breaking probability
KAPUTT_WSK = 10
JAESPA_MZ = 0.98
GZ_200_MZ = 0.85
FZ12_MZ = 0  # TODO: get value
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

# ruestungszeit
RUESTUNGS_ZEIT = 0

# unilokk created
UNILOKK_COUNT = 0


# global helper functions
def get_machines_for_part(part_name):
    #  returns the machines required to create a certain part of Unilokk
    match part_name:
        case "Oberteil":
            return OBERTEIL_MACHINES
        case "Unterteil":
            return UNTERTEIL_MACHINES
        case "Halteteil":
            return HALTETEIL_MACHINES
        case "Ring":
            return RING_MACHINES


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


def decrease_jobs(part_name):
    jobs = get_jobs_for_part(part_name)

    for job in jobs:
        if job.get_completed() >= 1:
            job.set_completed(job.get_completed() - 1)

        else:
            job.set_completed(0)


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
    elif machine == machine_arbeitsplatz or machine == machine_arbeitsplatz_2:
        return 1
    else:
        return 1
    # TODO: FZ12 left, also the MZ in Ring production to be checked


def get_quality_grade(machine):
    # returns the quality grade of parts created by certain machine
    # i.e if quality grade is 98%, it means 98% of material produced are usable to the next stage
    # 2% are thrown away
    if machine == machine_jaespa:
        return 1
    elif machine == machine_gz200:
        return 0.98
    elif machine == machine_fz12:
        return 0.95
    elif machine == machine_arbeitsplatz_2:
        return 0.85
    else:
        return 1


def orders_fulfilled(orders_received, unilokk):
    return (unilokk / orders_received) * 100


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


def get_parts_needed(orders_list):
    # receives orders and sets the universal variables OBERTEIL_ORDER,
    # UNTERTEIL_ORDER, HALTETEIL_ORDER, RING_ORDER
    total_parts = 0

    for order in orders_list:
        total_parts += order.amount

    global OBERTEIL_ORDER
    OBERTEIL_ORDER = total_parts
    global UNTERTEIL_ORDER
    UNTERTEIL_ORDER = total_parts
    global HALTETEIL_ORDER
    HALTETEIL_ORDER = total_parts
    global RING_ORDER
    RING_ORDER = total_parts

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
        self.done_once = False  # if true means the machine GZ200 in Ring creation has already been operated once
        self.orders = OrderList()  # custom data type to receive orders, initially Null

    # operation
    def operation(self, machine, operating_time):
        #  simulates an operation, it is an abstract function

        # operating machine after equipping
        while operating_time:
            start = self.env.now
            try:
                print(f"execution time is {operating_time} seconds, started execution at {self.env.now}")
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
    def get_ruestung_zeit(self, machine):
        # returns the equipping time in minutes as integer
        if machine == machine_fz12:
            return 30 * 60

        elif machine == machine_gz200:
            if self.previously_created == "":
                return 0
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Oberteil"):
                return 0
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Unterteil"):
                return 45 * 60
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Halteteil"):
                return 40 * 60
            elif (self.previously_created == "Oberteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Unterteil") and (self.next_creating == "Oberteil"):
                return 45 * 60
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Unterteil"):
                return 0
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Halteteil"):
                return 40 * 60
            elif (self.previously_created == "Unterteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Halteteil") and (self.next_creating == "Oberteil"):
                return 40 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Unterteil"):
                return 40 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Halteteil"):
                return 0 * 60
            elif (self.previously_created == "Halteteil") and (self.next_creating == "Ring"):
                return 45 * 60

            elif (self.previously_created == "Ring") and (self.next_creating == "Oberteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Unterteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Halteteil"):
                return 45 * 60
            elif (self.previously_created == "Ring") and (self.next_creating == "Ring"):
                return 0

        elif machine == machine_jaespa:
            return 0

        elif (machine == machine_arbeitsplatz) or (machine == machine_arbeitsplatz_2):
            return 0

    def get_operating_time(self, machine, part_name):
        #  returns the operating time for a certain machine on a specific Unilokk part
        match part_name:
            case "Oberteil":
                if machine == machine_jaespa:
                    return 34
                elif machine == machine_gz200:
                    return 287
                elif machine == machine_fz12:
                    return 376

            case "Unterteil":
                if machine == machine_jaespa:
                    return 20
                elif machine == machine_gz200:
                    return 247

            case "Halteteil":
                if machine == machine_jaespa:
                    return 4
                elif machine == machine_gz200:
                    return 255

            case "Ring":
                if machine == machine_jaespa:
                    return 3
                elif machine == machine_gz200:
                    match self.done_once:
                        case True:
                            return 10
                        case False:
                            return 185
                elif machine == machine_arbeitsplatz:
                    return 10

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

    def do_job(self, job, part_name):
        # performs a certain job as subprocess in part creation process
        # input amount is passed to diminish it based on machine's Qualitätsgrad after this job is done
        self.next_creating = part_name

        required_machine = job.get_machine_required()
        equipping_time = self.get_ruestung_zeit(required_machine)
        operating_time = job.get_duration()
        global RUESTUNGS_ZEIT
        RUESTUNGS_ZEIT += equipping_time  # collect Ruestungszeit for statistical purposes

        with required_machine.request(priority=1, preempt=False) as request:
            yield request
            yield self.env.timeout(equipping_time)
            self.process = self.env.process(self.operation(required_machine, operating_time))  # operating machinery
            self.env.process(self.break_machine(required_machine, 2, True))  # starting breakdown function
            yield self.process

            self.process = None

        if required_machine == machine_gz200:
            self.previously_created = part_name  # setting the control for get_ruestung_zeit function
        if part_name == "Ring":
            self.done_once = not self.done_once  # setting control for get_operating_time function

        # creating cumulative mz
        job.set_cumulative_mz(get_mz(required_machine))
        print("cumulative_mz ", job.get_cumulative_mz())

        if job.job_before is not None and job.job_before.get_completed():
            job.set_cumulative_mz(job.get_cumulative_mz() * job.job_before.get_cumulative_mz())

    def finish_unilokk_creation(self):
        # simulates the Kleben, Montage, Pruefen and Verpacken processes
        # after parts have been created
        print("\nFinishing process has started")

        n = 1
        # then assemble them into Unilokk
        while True:
            if OBERTEIL_COUNT > 0 and UNTERTEIL_COUNT > 0 and HALTETEIL_COUNT > 0 and RING_COUNT > 0:
                yield self.env.process(self.operation(machine_arbeitsplatz_2, 180))

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

    def fulfill_orders(self, orders):
        # the whole process from part creation to order fulfillment

        # receiving and prioritising orders
        self.orders.receive_order(orders)
        prioritized_list = self.orders.get_order_by_priority()
        parts_needed = get_parts_needed(prioritized_list)

        execution_sequence = amount_of_runs(parts_needed)
        print("execution sequence", execution_sequence)
        execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
        print("execution sequence by parts", execution_sequence_in_parts)

        # parts creation
        jobs = []  # array of jobs

        for part in execution_sequence_in_parts:
            jobs_for_part = get_jobs_for_part(part)

            # unpacking jobs into one list full of all the jobs
            for job in jobs_for_part:
                jobs.append(job)

        # TODO Optimizer runs here, orders jobs in jobs in the order with minimal Ruestungszeiten

        # why running loop again? because an optimizer will bee ran before here to determine the best
        # order or jobs for minimal Ruestungszeiten
        for job in jobs:
            # check if job required to be done before this is done
            if job.get_job_before() is not None and job.get_job_before().get_completed() <= 0:
                print(job.get_job_before().get_name(), " has to be done before ", job.get_name())
                jobs.insert(jobs.index(job.get_job_before()) + 1, job)  # inserting job after its prerequisite
            else:
                part_name = job.get_part_name()
                this_amount = get_output_per_part(part_name)
                yield self.env.process(self.do_job(job, part_name))

                job.set_completed(job.get_completed() + 1)  # incrementing times the job is done

                if all_jobs_completed_for_part(part_name):
                    #  all machines required to produce a part have been operated
                    # part is created
                    this_amount *= job.get_cumulative_mz()
                    increase_part_count(part_name, math.floor(this_amount))  # add newly created part

                    # decrease_jobs(part_name)

                    print(math.floor(this_amount), part_name, "(s) was created at ", self.env.now, "\n")

        # assembling parts
        yield self.env.process(self.finish_unilokk_creation())


# instantiate object of Lernfabrik class
env = simpy.Environment()

# instantiate machines as simpy resources
machine_jaespa = simpy.PreemptiveResource(env, capacity=1)  # Maschine zum Saegen
machine_gz200 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Drehen
machine_fz12 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Fräsen
machine_arbeitsplatz = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage
machine_arbeitsplatz_2 = simpy.PreemptiveResource(env, capacity=1)  # Machine zum Montage

# machines for part creation
OBERTEIL_MACHINES = [machine_jaespa, machine_gz200, machine_fz12]
UNTERTEIL_MACHINES = [machine_jaespa, machine_gz200]
HALTETEIL_MACHINES = [machine_jaespa, machine_gz200]
RING_MACHINES = [machine_jaespa, machine_gz200, machine_arbeitsplatz, machine_gz200]

# instantiating jobs
# Oberteil creation jobs
Oberteil_Saegen = Job("Oberteil_Saegen", "Oberteil", 34, machine_jaespa)
Oberteil_Drehen = Job("Oberteil_Drehen", "Oberteil", 287, machine_gz200)
Oberteil_Fraesen = Job("Oberteil_Fraesen", "Oberteil", 376, machine_fz12)
Oberteil_Saegen.set_job_before(None)
Oberteil_Saegen.set_job_after(Oberteil_Drehen)
Oberteil_Drehen.set_job_before(Oberteil_Saegen)
Oberteil_Drehen.set_job_after(Oberteil_Fraesen)
Oberteil_Fraesen.set_job_before(Oberteil_Drehen)
Oberteil_Fraesen.set_job_after(None)
Oberteil_Jobs = [Oberteil_Saegen, Oberteil_Drehen, Oberteil_Fraesen]

# Unterteil creation jobs
Unterteil_Saegen = Job("Unterteil_Saegen", "Unterteil", 20, machine_jaespa)
Unterteil_Drehen = Job("Unterteil_Drehen", "Unterteil", 247, machine_gz200)
Unterteil_Saegen.set_job_before(None)
Unterteil_Saegen.set_job_after(Unterteil_Drehen)
Unterteil_Drehen.set_job_before(Unterteil_Saegen)
Unterteil_Drehen.set_job_after(None)
Unterteil_Jobs = [Unterteil_Saegen, Unterteil_Drehen]

# Halteteil creation jobs
Halteteil_Saegen = Job("Halteteil_Saegen", "Halteteil", 4, machine_jaespa)
Halteteil_Drehen = Job("Halteteil_Drehen", "Halteteil", 255, machine_gz200)
Halteteil_Saegen.set_job_before(None)
Halteteil_Saegen.set_job_after(Halteteil_Drehen)
Halteteil_Drehen.set_job_before(Halteteil_Saegen)
Halteteil_Drehen.set_job_after(None)
Halteteil_Jobs = [Halteteil_Saegen, Halteteil_Drehen]

# Ring creation jobs
Ring_Saegen = Job("Ring_Saegen", "Ring", 3, machine_jaespa)
Ring_Drehen = Job("Ring_Drehen", "Ring", 185, machine_gz200)
Ring_Senken_1 = Job("Ring_Senken_1", "Ring", 10, machine_arbeitsplatz)
Ring_Senken_2 = Job("Ring_Senken_2", "Ring", 10, machine_gz200)
Ring_Saegen.set_job_before(None)
Ring_Saegen.set_job_after(Ring_Drehen)
Ring_Drehen.set_job_before(Ring_Saegen)
Ring_Drehen.set_job_after(Ring_Senken_1)
Ring_Senken_1.set_job_before(Ring_Drehen)
Ring_Senken_1.set_job_after(Ring_Senken_2)
Ring_Senken_2.set_job_before(Ring_Senken_1)
Ring_Senken_2.set_job_after(None)
Ring_Jobs = [Ring_Saegen, Ring_Drehen, Ring_Senken_1, Ring_Senken_2]

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

#order_list = OrderList(orders)

#prioritized_list = order_list.get_order_by_priority()

#for order in prioritized_list:
    #print(order.delivery_date)


# submitting order
#parts_needed = submit_order([1, 3, 4, 2, 6, 1, 3])
#print(parts_needed)
#execution_sequence = amount_of_runs(parts_needed)
#print("execution sequence", execution_sequence)
#execution_sequence_in_parts = get_parts_by_sequence(execution_sequence)
#print("execution sequence by parts", execution_sequence_in_parts)

env.process(fabric.fulfill_orders(orders))
env.run(until=SIM_TIME)

# analysis and results
print("\nOBERTEIL: ", OBERTEIL_COUNT)
print("UNTERTEIL: ", UNTERTEIL_COUNT)
print("HALTETEIL: ", HALTETEIL_COUNT)
print("RING: ", RING_COUNT, "\n")

print("required: ", OBERTEIL_ORDER, " produced: ", UNILOKK_COUNT)
print("orders fulfilled: ", orders_fulfilled(OBERTEIL_ORDER, UNILOKK_COUNT), "%")
print("total ruestungszeit: ", RUESTUNGS_ZEIT, "\n")

