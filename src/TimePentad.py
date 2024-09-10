pentads_per_year = 73

class TimePentad:

    def __init__(self, *args, **kwargs):#year: int, pentad: int):
 
        if "year" in kwargs or "pentad" in kwargs:

            if "year" not in kwargs:
                kwargs["year"] = 0

            elif "pentad" not in kwargs:
                kwargs["pentad"] = 0

            year = kwargs["year"]
            pentad = kwargs["pentad"]
        
        elif type(args[0]) == TimePentad:
            
            year = args[0].year
            pentad = args[0].pentad

        else:
            
            pentad_split = args[0].split("P")
            
            year = int(pentad_split[0], base=10)
            pentad = int(pentad_split[1], base=10)

        
        if pentad < 0 or pentad > 72:
            raise Exception("Pentad should be 0~72. Now it is %d" % (pentad,)) 

        self.year = year
        self.pentad = pentad



    def __add__(self, dpd):
       
        return Pentads2TimePentad(
            TimePentad2Pentads(self) + dpd.pentads
        )

    def __sub__(self, dt):

        if type(dt) == TimePentad:
            return Pentads2PentadDelta(
                TimePentad2Pentads(self) - TimePentad2Pentads(self)
            )

        elif type(dt) == PentadDelta: 
            return Pentads2TimePentad(
                TimePentad2Pentads(self) + dpd.pentads
            )


    def __str__(self):
        return "%dP%02d" % (self.year, self.pentad)


class PentadDelta:
 
    def __init__(self, *args, **kwargs):

        if "years" in kwargs or "pentads" in kwargs:

            if "years" not in kwargs:
                kwargs["years"] = 0

            elif "pentads" not in args:
                kwargs["pentads"] = 0

            years = kwargs["years"]
            pentads = kwargs["pentads"]
 
        elif type(args[0]) == PentadDelta:
            
            years = args[0].years
            pentads = args[0].pentads
       
        else:
            
            pentad_split = args[0].split("P")
            
            years = int(pentad_split[0], base=10)
            pentads = int(pentad_split[1], base=10)

        
        if pentads <= 0 or pentads > 72:
            raise Exception("Pentads should be 0~72") 

        self.pentads = years * pentads_per_year + pentads




   
def pentad_range(beg_tp, end_tp, inclusive="left"):
    
    beg_p = TimePentad2Pentads(TimePentad(beg_tp))
    end_p = TimePentad2Pentads(TimePentad(end_tp))

    if inclusive == "left":
        pass
    elif inclusive == "right":
        beg_p += 1
        end_p += 1
    elif inclusive == "both":
        end_p += 1
    elif inclusive == "neither":
        beg_p += 1

    for i in range(beg_p, end_p): 
        yield Pentads2TimePentad(i)
        
    
def TimePentad2Pentads(tp: TimePentad):
    
    return tp.year * pentads_per_year + tp.pentad

def Pentads2TimePentad(p: int):

    return TimePentad(
        year = p // pentads_per_year,
        pentad = p % pentads_per_year,
    )



