import threading
import time
import random

class Process:
    def __init__(self, pid, size, time_to_run):
        self.pid = pid
        self.size = size
        self.time_to_run = time_to_run

class MemoryManager:
    def __init__(self, total_memory):
        self.memory_map = []

    def initialize_memory(self):
        block_sizes = [8, 8, 6, 6, 6, 6, 4, 4, 4, 4, 2, 2, 2, 2]
        pid,p_size = 0,0
        for index, size in enumerate(block_sizes, start=1):
            self.memory_map.append([index, size, "free", pid,p_size])

    def allocate_memory(self, process):
        for block in self.memory_map:
            index, size, status, pid,p_size = block
            if status == "free" and size >= process.size:
                block[2] = "blocked"
                block[3] = process.pid
                block[4]=process.size
                return index
        # Если подходящей ячейки не найдено, пытаемся переместить другие процессы
        for block1 in self.memory_map:
            index1, size1, status1, pid1,p_size1= block1
            for block2 in self.memory_map:
                index2, size2, status2, pid2, p_size2 = block2
                if status=="free" and size2>=p_size1 and index1!=index2:
                    block2[2]="blocked"
                    block2[3]=pid1
                    block2[4]=p_size1
                    block1[3]=process.pid
                    block1[4]=process.size
                    return block1[0]
        return -1  # Allocation failed

    def free_memory(self, index):
        self.memory_map[index-1][2] = "free"
        self.memory_map[index-1][3] = 0
        self.memory_map[index-1][4] = 0

    def active_memory(self):
        count_memory=0
        active_cells=0
        for block in self.memory_map:
            count_memory+=block[4]
            if block[2]=="blocked":
                active_cells+=1
        return count_memory,active_cells


def run_process(process, memory_manager, completed_processes):
    while True:
        start_time = time.time()
        allocated_memory = memory_manager.allocate_memory(process)
        if allocated_memory != -1:
            time.sleep(process.time_to_run)
            memory_manager.free_memory(allocated_memory)
            completed_processes.append(process)
            break
        else:
            time.sleep(1)


def monitor_processes(completed_processes,memory_manager):
    t=0
    while True:
        mem,cells=memory_manager.active_memory()
        print(f"Работающие процессы: {1000-len(completed_processes)}, Завершенные процессы: {len(completed_processes)},"
              f"Занятая память: {mem}, Занятые ячейки: {cells}, Время работы: {t} секунд")
        t+=1
        time.sleep(1)
        # Проверяем, завершились ли все процессы
        if len(completed_processes) == 1000:
            break

def main():
    total_memory = 64

    memory_manager = MemoryManager(total_memory)
    memory_manager.initialize_memory()

    completed_processes = []

    processes = [Process(pid + 1, random.choice([2, 4, 6,8]), random.randint(5, 10)) for pid in range(1000)]

    threads = []

    start_time = time.time()

    monitor_thread = threading.Thread(target=monitor_processes, args=(completed_processes,memory_manager))
    monitor_thread.start()

    for process in processes:
        thread = threading.Thread(target=run_process, args=(process, memory_manager, completed_processes))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    monitor_thread.join()

    elapsed_time = time.time() - start_time
    print(f"Программа завершилась за  {round(elapsed_time,0)} секунды")

if __name__ == "__main__":
    main()





