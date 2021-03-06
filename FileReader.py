"""
FileReader.py, Author: jbr185, 66360439, dwa110, 28749539

this file contains functions for reading config files
"""
from MyUtils import checkParameter
from Link import Link

def readConfig(filePath):
    try:
        routerID = -1 #the router id for out daemon
        inputPorts = [] #the input ports we are listening to
        outputLinks = [] #the output connections we are sending to
        otherRouterIDs = [] #for keeping track of the router IDs we have to ensure no duplicates
        periodic_update_time = 30 #if not specified the periodic update time will default to 30 sec

        #open the file for reading
        file = open(filePath, 'r')
        text = file.readlines()
        file.close()

        #for each line in the file
        for (index, line) in enumerate(text):
            line = line.strip() #remove any leading whitespace

            if len(line) == 0:
                continue #empty line
            elif line.startswith('#'): 
                continue #comment line
            elif line.startswith("router-id"):
                line = line.split(' ') #brake apart the two parts of this line, the second is our router id!

                routerID = checkParameter(line[1], int, 0, 64001) #bound between 1 and 64000 inclusive
                otherRouterIDs.append(routerID) #we don't want people using our ID withut some complaints
            elif line.startswith("input-ports"):
                line = line[line.find(' '):].split(',') #split after the "input-ports" sub string

                for interface in line: #check each port input
                    interface = checkParameter(interface, int, 1023, 64001) #bound between 1024 and 64000 inclusive
                                       
                    if not (interface in inputPorts) and not (interface in [output.port for output in outputLinks]): #ensure its unique
                        inputPorts.append(interface)
                    else:
                        raise ValueError("Inferface socket port {} already in use".format(interface))
                    
            elif line.startswith("outputs"):
                line = line[line.find(' '):].split(',') #split after "outputs"

                for output in line:
                    link = Link() #we need a containing link object
                    output = output.split('-') #split the parts of each output
                    output[0] = checkParameter(output[0], int, 1023, 64001)
                    
                    if not (output[0] in [output.port for output in outputLinks]) and not (output[0] in inputPorts):
                        link.port = output[0]
                    else:
                        raise ValueError("Inferface socket port {} already in use".format(output[0]))
                        
                    link.metric = checkParameter(output[1], int, -1, 15) #second is the metric
                    output[2] = checkParameter(output[2], int, 0, 64001)
                    if not (output[2] in otherRouterIDs): #final is unique router id
                        otherRouterIDs.append(output[2])
                        link.routerID = output[2]
                    else:
                        raise ValueError("Router ID {} is duplicated in the configuration file. Router IDs must be unique.".format(output[2]))                    
            
                    outputLinks.append(link) #add the link port to the outputs
                    
            elif line.startswith("periodic-update-time"):
                line = line[line.find(' '):]
                periodic_update_time = checkParameter(line, int, 4, 1800)
                
            else: #the line is starting with something unknown
                raise SyntaxError("Syntax error in file \"{0}\", on line {1}".format(filePath, index + 1))
            
        if routerID == -1 or len(outputLinks) == 0 or len(inputPorts) == 0:
            raise ValueError("router-id, outputs and input-ports must all be specified in the file")
            
        return (routerID, inputPorts, outputLinks, periodic_update_time) #return the information in the file
    
    except (ValueError, TypeError) as error: #if we have some value or type error we have a syntax error in the file
        raise SyntaxError("Syntax error in file \"{0}\", on line {1}\nError: {2}".format(filePath, index + 1, error))
