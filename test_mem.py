import os
import gc

print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free())
s = gc.mem_free()

class C(object):
    def __init__(self, n):
        self.n = n
        
print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - s)
s = gc.mem_free()
        
def test(n):
    n+=1
    print(n)

if __name__ == "__main__":
    print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - s)
    s = gc.mem_free()
    a = [2 for i in range(1000)]
    print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - s)
    s = gc.mem_free()
    b = {}
    for i in range(1000):
        b[i] = 2
    print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - s)
    s = gc.mem_free()
    c = []
    for i in range(1000):
        c.append(C(2))
    print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free() - s)
    
