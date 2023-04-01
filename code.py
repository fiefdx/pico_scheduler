import os
import gc

from scheduler import Scheluder, Condition, Task, Message
from common import path_join, ticks_ms, ticks_add, ticks_diff, sleep_ms


def monitor(task, name, scheduler = None, display_id = None):
    while True:
        gc.collect()
        monitor_msg = "CPU:%3d%%  RAM:%3d%%" % (int(100 - scheduler.idle), int(100 - (scheduler.mem_free() * 100 / (264 * 1024))))
        yield Condition(sleep = 2000, send_msgs = [Message({"msg": monitor_msg}, receiver = display_id)])


def display(task, name):
    while True:
        yield Condition(sleep = 0, wait_msg = True)
        msg = task.get_message()
        print(msg.content["msg"])


def counter(task, name, interval = 100, display_id = None):
    n = 0
    while True:
        if n % 100 == 0:
            yield Condition(sleep = interval, send_msgs = [Message({"msg": "counter: %06d" % n}, receiver = display_id)])
        else:
            yield Condition(sleep = interval)
        n += 1


if __name__ == "__main__":
    try:
        s = Scheluder()
        display_id = s.add_task(Task(display, "display"))
        monitor_id = s.add_task(Task(monitor, "monitor", kwargs = {"scheduler": s, "display_id": display_id}))
        counter_id = s.add_task(Task(counter, "counter", kwargs = {"interval": 10, "display_id": display_id}))
        s.run()
    except Exception as e:
        print("main: %s" % str(e))
