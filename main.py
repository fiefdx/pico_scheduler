import os
import gc
machine = None
try:
    import machine
except:
    print("no machine module support")
thread = None
try:
    import _thread as thread
except:
    print("no multi-threading module support")

from scheduler import Scheluder, Condition, Task, Message
from common import path_join, ticks_ms, ticks_add, ticks_diff, sleep_ms, sha1sum

if machine:
    machine.freq(200000000)
    print("freq: %s mhz" % (machine.freq() / 1000000))

def monitor(task, name, scheduler = None, display_id = None):
    while True:
        gc.collect()
        monitor_msg = "CPU%s:%3d%%  RAM:%3d%%" % (scheduler.cpu, int(100 - scheduler.idle), int(100 - (scheduler.mem_free() * 100 / (264 * 1024))))
        yield Condition(sleep = 2000, send_msgs = [Message({"msg": monitor_msg}, receiver = display_id)])


def display(task, name):
    while True:
        yield Condition(sleep = 0, wait_msg = True)
        msg = task.get_message()
        print(msg.content["msg"])
        #print(sha1sum("test"))


def counter(task, name, interval = 100, display_id = None):
    n = 0
    while True:
        if n % 100 == 0:
            yield Condition(sleep = interval, send_msgs = [Message({"msg": "counter: %06d" % n}, receiver = display_id)])
        else:
            yield Condition(sleep = interval)
        n += 1


def core1_thread(scheduler):
    scheduler.run()
    print("core1: exit")


if __name__ == "__main__":
    s1 = None
    if thread:
        s1 = Scheluder(cpu = 1)
    try:
        if s1:
            display_id = s1.add_task(Task(display, "display"))
            monitor_id = s1.add_task(Task(monitor, "monitor", kwargs = {"scheduler": s1, "display_id": display_id}))
            counter_id = s1.add_task(Task(counter, "counter", kwargs = {"interval": 10, "display_id": display_id}))
            second_thread = thread.start_new_thread(core1_thread, (s1,))
        s = Scheluder(cpu = 0)
        display_id = s.add_task(Task(display, "display"))
        monitor_id = s.add_task(Task(monitor, "monitor", kwargs = {"scheduler": s, "display_id": display_id}))
        counter_id = s.add_task(Task(counter, "counter", kwargs = {"interval": 10, "display_id": display_id}))
        s.run()
    except Exception as e:
        if s1:
            s1.stop = True
        print("main: %s" % str(e))
