import os
import gc
import time
machine = None
microcontroller = None
try:
    import machine
except:
    try:
        import microcontroller
    except:
        print("no machine & microcontroller module support")
thread = None
try:
    import _thread as thread
except:
    print("no multi-threading module support")

from scheduler import Scheluder, Condition, Task, Message
from common import ticks_ms, ticks_add, ticks_diff, sleep_ms

if machine:
    machine.freq(240000000)
    print("freq: %s mhz" % (machine.freq() / 1000000))
if microcontroller:
    microcontroller.cpu.frequency = 240000000
    print("freq: %s mhz" % (microcontroller.cpu.frequency / 1000000))

def monitor(task, name, scheduler = None, display_id = None):
    while True:
        gc.collect()
        ram_free = gc.mem_free()
        ram_used = gc.mem_alloc()
        monitor_msg = "CPU%s:%3d%%  RAM:%3d%%\nR%6.2f%%|F%7.2fk/%d|U%7.2fk/%d\nMessages: %s|Conditions: %s|Tasks: %s" % (
                                                          scheduler.cpu,
                                                          int(100 - scheduler.idle),
                                                          int(100 - (scheduler.mem_free() * 100 / (264 * 1024))),
                                                          100.0 - (ram_free * 100 / (264 * 1024)),
                                                          ram_free / 1024,
                                                          ram_free,
                                                          ram_used / 1024,
                                                          ram_used,
                                                          Message.remain(),
                                                          Condition.remain(),
                                                          Task.remain())
        yield Condition(sleep = 2000, send_msgs = [Message.get().load({"msg": monitor_msg}, receiver = display_id)])


def display(task, name):
    while True:
        yield Condition(sleep = 0, wait_msg = True)
        msg = task.get_message()
        print(msg.content["msg"])
        msg.release()


def counter(task, name, interval = 100, display_id = None):
    n = 0
    while True:
        if n % 100 == 0:
            yield Condition.get().load(sleep = interval, send_msgs = [Message.get().load({"msg": "%s: %06d" % (name, n)}, receiver = display_id)])
        else:
            yield Condition.get().load(sleep = interval)
        n += 1

if __name__ == "__main__":
    print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free())
    ss = gc.mem_free()
    Message.init_pool(25)
    Condition.init_pool(15)
    Task.init_pool(15)
    try:
        s = Scheluder(cpu = 0)
        display_id = s.add_task(Task.get().load(display, "display", condition = Condition.get()))
        monitor_id = s.add_task(Task.get().load(monitor, "monitor", condition = Condition.get(), kwargs = {"scheduler": s, "display_id": display_id}))
        counter_id = s.add_task(Task.get().load(counter, "counter_cpu0", condition = Condition.get(), kwargs = {"interval": 10, "display_id": display_id}))
        print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - ss)
        s.run()
    except Exception as e:
        print("main: %s" % str(e))
    print("core0 exit")