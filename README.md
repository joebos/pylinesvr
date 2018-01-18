# pylinesvr
Line Server - Python implementation


<p>Python implementation: https://github.com/joebos/pylineserver</p>
<p>Golang implementation: https://github.com/joebos/golinesvr  (This repo)</p>

<p>Load testing tool (Go): https://github.com/joebos/goloadtester</p>

Environment (developed and tested):
go version go1.9.2 linux/amd64
pip 9.0.1 from /home/white/env27b/lib/python2.7/site-packages (python 2.7)


# Line Server written in Go
<h2>1. How does your system work? (if not addressed in comments in source)</h2>

The system listens the TCP port, and accept connection from clients, and then call a goroutine to hanle any new connection on a seperate thread so other clients can make connection to the system too.

This is same as the typical HTTP server architecture - spawn a new thread for every connection so not to block the main thread. Some HTTP servers would fork a new process instead of new thread to handle each connection. The cost of a thread is much smaller than a process in terms of memory and CPU usage.

I originally planned to write the system just in Python. After I wrote a load test to test my Python line server, and learned a great deal of goroutine/channel as such a simple way to implement concurrency. I became interested in what would be the difference between Go and Python if I write the same system in both language, so I wrote both. And this is the Go version. A goroutine runs on thread so this implementation uses thread too.

In terms of handling text file, the system pre-processes it and builds an index first. The index is similar to the cluster index we see in relational database. The key (primary key) is the line number, and the value is the file offset of a line from the start of the text file. 

In order to deal with a large number of lines where all the line numbers could not fit in memory, the system splits the index into index page files. Each index page file stores the file offsets for m number of lines (m is configurable in configuration.go). If a text file has more than m lines, the system does n/m to determine which index file, and use n % m to determine the index(file offset) for line n.

<h2>2. How will your system perform as the number of requests per second increases?</h2>

Go Line Server performance          |  Python Line Server performance
:-------------------------:|:-------------------------:
![Go Line server load test result](https://github.com/joebos/golinesvr/blob/master/GoLineServer50M1M.png)  |  ![Python Line server load test result](https://github.com/joebos/golinesvr/blob/master/PyLineServer50M1M.png)

From the above performance charts, we can see that Go performs more consistently than Python. The longest times taken for Python line server is about 10 times than averages, whereas for Go line server about 2-3 times than averages. The reason why Python max times are bigger is because of creating and closing processes. However, on average, Python takes less time than Go. I could have implemented line server using python thread, however, Python has GIL lock, i.e. code can only run one at time. There is no real thread concurrency in Python.
If client connection is long lived, forking processes performs better for most of user requests. However, if client connection is short lived, threading model performs better.


<h2>3. How will your system perform with a 1 GB file? a 10 GB file? a 100 GB file?</h2>


Go Line Server performance - 50M file         |  Go Line Server performance - 10G file
:-------------------------:|:-------------------------:
![Go Line server load test result](https://github.com/joebos/golinesvr/blob/master/GoLineServer50M1M.png)  |  ![Python Line server load test result](https://github.com/joebos/golinesvr/blob/master/GoLineServer10G11M.png)

As the file gets bigger, Go line server takes more time to respond.

Python Line Server performance - 50M file         |  Python Line Server performance - 10G file
:-------------------------:|:-------------------------:
![Python Line server load test result](https://github.com/joebos/golinesvr/blob/master/PyLineServer50M1M.png)  |  ![Python Line server load test result](https://github.com/joebos/golinesvr/blob/master/PyLineServer10G11M.png)

For Python line server, the performance is virtually not changed. Again, this is because of forking process. Python line server takes more cpu and resources because of all the child processes, thus it performs better than Go as the text file gets bigger.
For big files, perhaps we can use process + threading model. We can set limits on # of threads per process, once # of threads reaches the limit, we can fork new process. I think Python uwsgi has this process + thread model for http requests.


<h2>4. What documentation, websites, papers, etc did you consult in doing this assignment?</h2>

I wrote Python implementation first. So when I started Go implementation, I already have a design.

I searched Stack Overflow for code snippets, and how to code for certain things such as how to convert bytes to string and vice versa, go language syntax.

Go documentation website.

Google search for how to debug go and go test in VS code.

<h2>5. What third-party libraries or other tools does the system use?</h2>

Go libraries
Python SocketServer module

<h2>6. How long did you spend on this exercise?</h2>

Design: 8 hours
   Decide how to handle multiple clients (thread, process) and what to do with big text files (indexing for O(1) get operation)

Python implementation: 8 hours
   Implement the design in Python
   unit test Line File
   Use the load test I built in Go to do end to end testing.

GO implementation: 16 hours
   Implement the design in Go
   unit test Line File
   Use the load test I built in Go to do end to end testing. 
   I learned Go as I were coding.

Load test tool: 4 hours

<h2> 7. Further performance improvement thoughts </h2>
  
Loading index files take time. If a GET triggers loading a new index page file, there will be a performance hit on that GET. We could use database like MySQL to store page files as all database products are smart handling caching tables and indexes in general. However any database instance requires cpu and memory resources.

In terms of the architecture of processing user connections/requests, we can use process + thread model, if client connections are short lived, we can put higher limit on # of threads a process can have. If connections are long lived,lower limits on # of threads per process. In real production system, we can conduct through performance/load testing based on actual use cases and configure accordingly.

<h2> 8. Lessons learned </h2>

Go offers an incredible way for parallelism and concurrency. You could need to write tons of codes for concurrency programming in other languages like Python, C# and C++. But with Go, you just use a couple of keywords and you are pretty much done!

However, I felt that Python offer more easy way or intuitive way for common things such as string, bytes manipulations, and reading/writing files. Perhaps Go is still a pretty new language and its packages will be improved and become better.
