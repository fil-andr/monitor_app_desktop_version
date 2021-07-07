from tkinter import *
# import time
import sqlalchemy as sa
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
from tkinter.ttk import Combobox
import os
import platform
import re
import paramiko

## read conf file
if platform.system() == 'Windows':
    with open(rf'{os.path.dirname(__file__)}\host_mon.conf', 'r') as conf_file:
        hosts = conf_file.readlines()
if platform.system() == 'Linux':
    with open(rf'{os.path.dirname(__file__)}/host_mon.conf', 'r') as conf_file:
        hosts = conf_file.readlines()
hosts_2 = []
for i in hosts:
    hosts_2.append(re.sub('\n','',i))

hosts = hosts_2

hosts_conn = []
for i in hosts:
    hosts_conn.append(i.split(','))

#settings for paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


#load values from db for cpu graph
def db_cpu_usage():
    engine = sa.create_engine(f'postgresql://postgres:pswd_123@192.168.0.72:5432/postgres')
    ts_sel = engine.execute(f"select * from cpu_usg where host='{hosts_comb.get()}'")
    times = []
    mem_values = []
    time_values = []
    for i in ts_sel:
        times.append(i[0])
        mem_values.append(i[1])
    time_values.append(times)
    time_values.append(mem_values)
    return time_values


#load values from db for mem graph
def db_mem_usage():
    engine = sa.create_engine(f'postgresql://postgres:pswd_123@192.168.0.72:5432/postgres')
    ts_sel = engine.execute(f"select * from mem_usg where host='{hosts_comb.get()}'")
    times = []
    mem_values = []
    time_values = []
    for i in ts_sel:
        times.append(i[0])
        mem_values.append(i[1])
    time_values.append(times)
    time_values.append(mem_values)
    return time_values



def memory_usage():
    hostname, username, password = host_actual(hosts_comb.get())
    client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False,
                   timeout=3)
    stdin, stdout, stderr = client.exec_command("free -m | grep Mem:")
    mem_lst = ''.join(stdout.readlines()).split()
    d = round(int(mem_lst[2]) * 100 / int(mem_lst[1]))
    engine = sa.create_engine(f'postgresql://postgres:pswd_123@192.168.0.72:5432/postgres')
    engine.execute(f"INSERT INTO mem_usg (value,host) VALUES({d},'{hosts_comb.get()}')")
    return d

def cpu_usage():
    hostname, username, password = host_actual(hosts_comb.get())
    client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False,
                   timeout=3)
    stdin, stdout, stderr = client.exec_command("top -bn1 | grep %Cpu")
    cpu_lst = ''.join(stdout.readlines()).split()
    engine = sa.create_engine(f'postgresql://postgres:pswd_123@192.168.0.72:5432/postgres')
    engine.execute(f"INSERT INTO cpu_usg (value,host) VALUES({cpu_lst[1]},'{hosts_comb.get()}')")
    return cpu_lst


def dsk_usg():
    hostname, username, password = host_actual(hosts_comb.get())
    client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False,
                   timeout=3)
    stdin, stdout, stderr = client.exec_command(r"df -h | awk '{ print $5 "  " $6  }'")
    dsk_space_lst = ''.join(stdout.readlines()).split()
    dsk_space_lst.remove(dsk_space_lst[0])
    dsk_res = []
    res = 'DISK USAGE\n'
    for i in dsk_space_lst:
        dsk_res.append(i.split('%'))
    for i in dsk_res:
        res += f' {i[1]} --- use: {i[0]}%\n'
    return res


def io():
    hostname, username, password = host_actual(hosts_comb.get())
    client.connect(hostname=hostname, username=username, password=password, look_for_keys=False, allow_agent=False,
                   timeout=3)
    stdin, stdout, stderr = client.exec_command("iostat -xyd 1 1 | awk '{ print $14 " " $1 }'")
    lst = stdout.readlines()
    lst.remove(lst[0])
    lst.remove(lst[0])
    lst.remove(lst[0])
    lst.remove(lst[len(lst) - 1])
    val_prc = []
    for i in lst:
        d = re.findall(r'\d+\.\d+', i)
        val_prc.append(d)
    dsk = []
    for i in lst:
        g = re.sub('\d+\.\d+', '', i).strip('\n')
        dsk.append(g)
    result = 'DISKS STATS\n'
    tmp_val = 0
    while tmp_val <= len(dsk) - 1:
        result += f'{dsk[tmp_val]} | utl%: {val_prc[tmp_val][0]}\n'
        tmp_val += 1
    return result


def list_of_hosts():
    global hosts_for_comb
    hosts_for_comb = []
    for i in hosts_conn:
        hosts_for_comb.append(i[0])
    return hosts_for_comb


def host_actual(input_string):
    inp = input_string.strip('/')
    host_actual_con = []
    for i in hosts_conn:
        if inp in i:
            host_actual_con.append(i[0])
            host_actual_con.append(i[1])
            host_actual_con.append(i[2])
    return host_actual_con


def refresh():
    mem_lbl.configure(text=f"Memory usage:  {memory_usage()} %")
    cpu_usg_lbl.configure(text=f"CPU usage:  {cpu_usage()[1]} %")
    dsk_usg_lbl.configure(text=dsk_usg(), justify=LEFT)
    io_usg_lbl.configure(text=io(), justify=LEFT)


def cpu_graph():
    cpu_graph_window = Tk()
    cpu_graph_window.geometry('800x600')
    cpu_graph_window.title(f"CPU usage graph {hosts_comb.get()}")
    matplotlib.use('TkAgg')
    fig = plt.figure(1)
    canvas = FigureCanvasTkAgg(fig, master=cpu_graph_window)
    plot_widget = canvas.get_tk_widget()
    plot_widget.grid(row=0, column=0)
    plt.plot(db_cpu_usage()[0], db_cpu_usage()[1])


def mem_graph():
    mem_graph_window = Tk()
    mem_graph_window.geometry('800x600')
    mem_graph_window.title(f"MEM usage graph {hosts_comb.get()}")
    matplotlib.use('TkAgg')
    fig2 = plt.figure(2)
    canvas1 = FigureCanvasTkAgg(fig2, master=mem_graph_window)
    plot_widget3 = canvas1.get_tk_widget()
    plot_widget3.grid(row=0, column=0)
    plt.plot(db_mem_usage()[0], db_mem_usage()[1])


window = Tk()
window.geometry('600x600')
window.title("Host monitor")


hosts_comb = Combobox(window)
hosts_comb['values'] = (list_of_hosts())
hosts_comb.current(0)
hosts_comb.grid(column=3, row=8)

#mem usage label
mem_lbl = Label(window, text=f"Memory usage:  {memory_usage()} %")
mem_lbl.grid(column=0, row=0)


#cpu usage label
cpu_usg_lbl = Label(window, text=f"CPU usage:  {cpu_usage()[1]} %")
cpu_usg_lbl.grid(column=0, row=3)

#disk percesnt usage label
dsk_usg_lbl = Label(window, text=dsk_usg(), justify=LEFT)
dsk_usg_lbl.grid(column=0, row=17)


#io percesnt usage label
io_usg_lbl = Label(window, text=io(), justify=LEFT)
io_usg_lbl.grid(column=0, row=18)

##buttons

#refresh button
refresh_button = Button(window, text='Refresh', command=refresh)
refresh_button.grid(column=0, row=20)

#cpu graph button
graph_button = Button(window, text='CPU graph', command=cpu_graph)
graph_button.grid(column=0, row=4)

#mem graph button
graph_button_mem = Button(window, text='MEM graph', command=mem_graph)
graph_button_mem.grid(column=0, row=2)

window.mainloop()



