def func1():
    a = []
    count = 1
    fin = open('hashaudio.txt', 'r')
    for line in fin:
        if line != "" and line[0] == "A":
            a.append(line)
    fin.close()
    fin = open('hashaudio.txt', 'w')
    for i in a:
        fin.write(i + " " + str(count))
        count += 1
    fin.close()


def func2():
    count = 0
    f = open('file.txt', 'r')
    for line in f:
        if line != "\n":
            print(line.split(" ")[0])
            count += 1
    print("end count = " + str(count))


func2()
