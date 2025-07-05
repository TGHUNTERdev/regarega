import re
class Constructor:
    def __init__(self,template):
        self.template=re.compile(template)
    def replace(self,line):
        inner=self.template.search(line)
        if inner:
            return self.handle(line,inner)
    def handle(self,line,inner):
        raise NotImplementedError
class Synchronizer:
    def __init__(self,constructors):
        self.constructors=constructors
    def asynchronize(self,inpath,outpath):
        with open(outpath,"w") as outfile:
            with open(inpath) as infile:
                for line in infile:
                    tab=self.findtab(line)
                    if tab is not None:
                        outfile.write(" "*tab+self.replace(line[tab:])+"\n")
    def findtab(self,line):
        for index,char in enumerate(line):
            if char!=" ":
                return index
    def replace(self,line):
        line=line.rstrip()
        for constructor in self.constructors:
            result=constructor.replace(line)
            if result:
                return result
        return line
    
##asynchronizer
class AsyncDefAction(Constructor):
    def handle(self,line,inner):
        return f"async {line}"
class AsyncClientApi(Constructor):
    def handle(self,line,inner):
        return line[:inner.start()]+"await "+inner[0]+line[inner.end():]
asynchronizer=Synchronizer([
    AsyncDefAction("^def registrate"),
    AsyncClientApi("action\("),
    AsyncDefAction("^def Action"),
    AsyncClientApi(r"account\.client\.\w+?\(")
])
asynchronizer.asynchronize(
    "Registrator.py",
    "RegistratorAsync.py"
)
