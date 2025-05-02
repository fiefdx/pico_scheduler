import gc
import sys

from common import ticks_ms, ticks_add, ticks_diff, sleep_ms


class Message(object):
    pool = []

    @classmethod
    def init_pool(cls, size = 100):
        for i in range(size):
            cls.pool.append(Message("", processed = True))

    @classmethod
    def get(cls):
        for m in cls.pool:
            if m.processed:
                m.processed = False
                return m
            
    @classmethod
    def remain(cls):
        n = 0
        for m in cls.pool:
            if m.processed:
                n += 1
        return n

    def __init__(self, content, sender = None, sender_name = "", receiver = None, processed = False):
        self.content = content
        self.sender = sender
        self.sender_name = sender_name
        self.receiver = receiver
        self.processed = processed

    def load(self, content, sender = None, sender_name = "", receiver = None):
        self.content = content
        self.sender = sender
        self.sender_name = sender_name
        self.receiver = receiver
        self.processed = False
        return self

    def release(self):
        del self.content
        self.content = ""
        self.sender = None
        del self.sender_name
        self.sender_name = ""
        self.receiver = None
        self.processed = True


class Condition(object):
    pool = []
    
    @classmethod
    def init_pool(cls, size = 100):
        for i in range(size):
            cls.pool.append(Condition(processed = True))

    @classmethod
    def get(cls):
        for c in cls.pool:
            if c.processed:
                c.resume_at = ticks_add(ticks_ms(), 0)
                c.wait_msg = False
                c.processed = False
                return c
            
    @classmethod
    def remain(cls):
        n = 0
        for c in cls.pool:
            if c.processed:
                n += 1
        return n
    
    def __init__(self, code = 0, sleep = 0, send_msgs = [], wait_msg = False, processed = False):
        self.code = code
        self.resume_at = ticks_add(ticks_ms(), sleep) # ms
        self.send_msgs = send_msgs
        self.wait_msg = wait_msg
        self.processed = processed
        
    def load(self, code = 0, sleep = 0, send_msgs = [], wait_msg = False):
        self.code = code
        self.resume_at = ticks_add(ticks_ms(), sleep) # ms
        self.send_msgs = send_msgs
        self.wait_msg = wait_msg
        self.processed = False
        return self
    
    def release(self):
        self.code = 0
        self.resume_at = 0
        del self.send_msgs
        self.send_msgs = []
        self.processed = True
        
        
class Task(object):
    pool = []
    id_count = 0

    @classmethod
    def init_pool(cls, size = 100):
        for i in range(size):
            cls.pool.append(Task(None, "", processed = True))

    @classmethod
    def get(cls):
        for t in cls.pool:
            if t.processed:
                t.processed = False
                return t
            
    @classmethod
    def remain(cls):
        n = 0
        for t in cls.pool:
            if t.processed:
                n += 1
        return n
    
    @classmethod
    def new_id(cls):
        cls.id_count += 1
        return cls.id_count
    
    def __init__(self, func, name, condition = None, task_id = None, args = [], kwargs = {}, need_to_clean = [], processed = False):
        self.id = Task.new_id()
        if task_id:
            self.id = task_id
        self.name = name
        self.msgs = []
        self.msgs_senders = []
        self.func = func(self, name, *args, **kwargs) if func else None
        self.condition = condition
        self.need_to_clean = need_to_clean
        self.processed = processed

    def load(self, func, name, condition = Condition(), task_id = None, args = [], kwargs = {}, need_to_clean = [], processed = False):
        self.id = Task.new_id()
        if task_id:
            self.id = task_id
        self.name = name
        self.msgs = []
        self.msgs_senders = []
        self.func = func(self, name, *args, **kwargs) if func else None
        self.condition = condition
        self.need_to_clean = need_to_clean
        self.processed = False
        return self
        
    def set_condition(self, condition):
        self.condition.release()
        self.condition = condition
        
    def put_message(self, message):
        self.msgs.append(message)
        self.msgs_senders.append(message.sender)
        
    def get_message(self, sender = None):
        msg = None
        try:
            if sender is None:
                msg = self.msgs.pop(0)
                _ = self.msgs_senders.pop(0)
            else:
                i = self.msgs_senders.index(sender)
                msg = self.msgs.pop(i)
                _ = self.msgs_senders.pop(i)
        except Exception as e:
            pass
        return msg
        
    def ready(self):
        if ticks_diff(ticks_ms(), self.condition.resume_at) >= 0:
            if self.condition.wait_msg is True:
                return len(self.msgs) > 0
            elif self.condition.wait_msg >= 1:
                return self.condition.wait_msg in self.msgs_senders
            else:
                return True
        else:
            return False
        
    def clean(self):
        del self.name
        for m in self.msgs:
            m.release()
        del self.msgs_senders
        del self.func
        if self.condition:
            self.condition.release()
        del self.need_to_clean
        self.processed = True


class Scheluder(object):
    def __init__(self, log_to = None, name = "scheduler", cpu = 0):
        self.log_to = log_to
        self.cpu = cpu
        self.name = name
        self.tasks = []
        self.tasks_ids = {}
        self.task_sort_at = 0
        self.current = None
        self.sleep_ms = 0
        self.load_calc_at = ticks_ms()
        self.idle = 0
        self.idle_sleep_interval = 0.1
        self.task_sleep_interval = 0.1
        self.need_to_sort = True
        self.stop = False
        
    def task_sort(self, task):
        if task.condition.wait_msg:
            if len(task.msgs) > 0:
                return -1000000
            else:
                return 1000000
        return ticks_diff(task.condition.resume_at, self.task_sort_at)

    def add_task(self, task):
        self.tasks.append(task)
        self.tasks_ids[task.id] = task
        return task.id

    def remove_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
        del self.tasks_ids[task.id]
        
    def exists_task(self, task_id):
        return task_id in self.tasks_ids
    
    def get_task(self, task_id):
        if task_id in self.tasks_ids:
            return self.tasks_ids[task_id]
        return None
        
    def send_msg(self, msg):
        self.msgs.put(msg)
        
    def mem_free(self):
        return gc.mem_free()
    
    def cpu_idle(self):
        return self.idle
    
    def set_log_to(self, task_id):
        self.log_to = task_id
    
    def log(self, content):
        if self.log_to:
            self.tasks_ids[self.log_to].put_message(Message.get().load(content, sender = 0, sender_name = self.name))
        else:
            print(content)

    def run(self):
        while not self.stop:
            try:
                load_interval = ticks_diff(ticks_ms(), self.load_calc_at)
                if load_interval >= 1000:
                    self.idle = self.sleep_ms * 100 / load_interval
                    if self.idle > 100:
                        self.idle = 100
                    self.sleep_ms = 0
                    self.load_calc_at = ticks_ms()
                if self.tasks:
                    #print(self.tasks)
                    if self.need_to_sort == True:
                        self.task_sort_at = ticks_ms()
                        self.tasks.sort(key = self.task_sort)
                        self.need_to_sort = False
                    if self.current is None:
                        peek = self.tasks[0]
                        now = ticks_ms()
                        if peek.ready():
                            # print("ready: %s" % peek.id)
                            self.current = self.tasks.pop(0)
                            try:
                                self.current.set_condition(next(self.current.func))
                                self.tasks.append(self.current)
                                for msg in self.current.condition.send_msgs:
                                    msg.sender = self.current.id
                                    msg.sender_name = self.current.name
                                    if msg.receiver in self.tasks_ids:
                                        self.tasks_ids[msg.receiver].put_message(msg)
                                self.current = None
                                self.need_to_sort = True
                            except StopIteration:
                                self.remove_task(self.current)
                                for m in self.current.need_to_clean:
                                    try:
                                        m_name = m.__name__
                                        exec("del %s" % m.__name__)
                                        # exec("del %s" % m.__name__.split(".")[-1])
                                        if hasattr(m, "main"):
                                            del m.main
                                        del sys.modules[m_name]
                                        gc.collect()
                                    except Exception as e:
                                        self.log("task: %s: %s" % (self.current.name, sys.print_exception(e)))
                                self.current.clean()
                                # del self.current
                                self.current = None
                            except TypeError:
                                if self.current:
                                    self.current.clean()
                                    # del self.current
                                self.current = None
                            except Exception as e:
                                self.log("task: %s: %s" % (self.current.name, sys.print_exception(e)))
                                if self.current:
                                    self.current.clean()
                                    # del self.current
                                self.current = None
                        else:
                            sleep_ms(self.task_sleep_interval)
                            self.sleep_ms += self.task_sleep_interval
                else:
                    sleep_ms(self.idle_sleep_interval)
                    self.sleep_ms += self.idle_sleep_interval
            except KeyboardInterrupt as e:
                self.log("scheduler exit: %s" % sys.print_exception(e))
                break
            except Exception as e:
                self.log("scheduler exit: %s" % sys.print_exception(e))
