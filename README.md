# Pico Scheduler

A python task scheduler for circuitpython & micropython


## Design

<b>Message</b>: A message to send to another task

<b>Condition</b>: A signal to yield to suspend current task and back to scheduler with/without sending messages to another task

<b>Task</b>: A function with forever loop and yield sentence, it do all the workload

<b>Scheduler</b>: A class with forever loop procedure, do all the scheduling work, operate all the communications between tasks, and, statistic memory and cpu load

![procedure](/doc/procedure.bmp?raw=true "procedure")


