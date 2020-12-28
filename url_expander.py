import queue
import threading
import time
import sys
from argparse import ArgumentParser

import requests

inqueue = queue.Queue()
outqueue = queue.Queue()

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, inqueue, outqueue):
        threading.Thread.__init__(self)
        self.in_queue = inqueue
        self.out_queue = outqueue

    def run(self):
        while True:
            #grabs host from queue
            host = self.in_queue.get()
            #host = self.in_queue.get(self)
            chunk = ""
            #grabs urls of hosts and then grabs chunk of webpage
            myurl = host
            try:
                #url = urllib2.urlopen(myurl, timeout=3)
                expanded_url = requests.head(myurl, allow_redirects=True, timeout=5)
                expanded_url = expanded_url.url
            except:
                #print('hit exception....')
                expanded_url = "UNABLE_TO_EXPAND"
                #pass
            chunk = host + "|" + expanded_url
            #place chunk into out queue
            self.out_queue.put(chunk)

            #signals to queue job is done
            self.in_queue.task_done()

class DatamineThread(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, out_queue, out_file):
        threading.Thread.__init__(self)
        self.out_queue = out_queue
        self.out_file = out_file

    def run(self):
        while True:
            #grabs host from queue
            chunk = self.out_queue.get()
            if chunk is not "":
                print(bcolors.YELLOW + chunk + bcolors.ENDC)
                if self.out_file is not None:
                    with open(self.out_file, "a") as f:
                        f.write(chunk + "\n")
            #signals to queue job is done
            self.out_queue.task_done()

def main():
    parser = ArgumentParser()
    parser.add_argument("-t", "--thread-count", nargs = '?', default = 3, type = int, help = "Custom number of threads for requests")
    parser.add_argument("-f", "--url-file", default = "./url_list.txt", help = "urllist newline separated")
    parser.add_argument("-o", "--output", default = None, help = "urllist newline separated")
    #parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    args = parser.parse_args()
    
    with open(args.url_file) as f:
        hosts = f.read().splitlines()

    #spawn a pool of threads, and pass them queue instance
    for i in range(args.thread_count):
        t = ThreadUrl(inqueue, outqueue)
        t.setDaemon(True)
        t.start()
    
    #populate queue with data
    for host in hosts:
        inqueue.put(host)
    
    # the threads for the writer, it only needs one really.    
    for i in range(20):
        dt = DatamineThread(outqueue,args.output)
        dt.setDaemon(True)
        dt.start()
    #wait on the queue until everything has been processed
    inqueue.join()
    outqueue.join()


if __name__ == '__main__':
    start = time.time()
    main()
    time_to_complete = time.time() - start
    print("Elapsed Time: %s seconds" % (round(time_to_complete,2)))
