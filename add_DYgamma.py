import collections
import re

if '__main__' == __name__:
    import sys
    sys.path.append('../../')
#if '__main__' == __name__:
 #   import sys
#    sys.path.append('/home/jhchoi/photos_standalone/180611/mg/MG5_aMC_v2_2_3')



import logging
logger = logging.getLogger("madgraph.lhe_parser")

class Particle(object):
    """ """
    pattern=re.compile(r'''^\s*
        (?P<pid>-?\d+)\s+           #PID
        (?P<status>-?\d+)\s+            #status (1 for output particle)
        (?P<mother1>-?\d+)\s+       #mother
        (?P<mother2>-?\d+)\s+       #mother
        (?P<color1>[+-e.\d]*)\s+    #color1
        (?P<color2>[+-e.\d]*)\s+    #color2
        (?P<px>[+-e.\d]*)\s+        #px
        (?P<py>[+-e.\d]*)\s+        #py
        (?P<pz>[+-e.\d]*)\s+        #pz
        (?P<E>[+-e.\d]*)\s+         #E
        (?P<mass>[+-e.\d]*)\s+      #mass
        (?P<vtim>[+-e.\d]*)\s+      #displace vertex
        (?P<helicity>[+-e.\d]*)\s*      #helicity
        ($|(?P<comment>\#[\d|D]*))  #comment/end of string
        ''',66) #verbose+ignore case
    
    
    
    def __init__(self, line=None, event=None):
        """ """
        
        self.event = event
        self.event_id = len(event) #not yet in the event
        # LHE information
        self.pid = 0
        self.status = 0
        self.mother1 = None
        self.mother2 = None
        self.color1 = 0
        self.color2 = None
        self.px = 0
        self.py = 0 
        self.pz = 0
        self.E = 0
        self.mass = 0
        self.vtim = 0
        self.helicity = 9
        self.comment = ''

        if line:
            self.parse(line)
            
    def parse(self, line):
        """parse the line"""
    
        obj = self.pattern.search(line)
        if not obj:
            raise Exception, 'the line\n%s\n is not a valid format for LHE particle' % line
        for key, value in obj.groupdict().items():
            if key not in  ['comment','pid']:
                setattr(self, key, float(value))
            elif key in ['pid', 'mother1', 'mother2']:
                setattr(self, key, int(value))
            else:
                self.comment = value
        # Note that mother1/mother2 will be modified by the Event parse function to replace the
        # integer by a pointer to the actual particle object.
    
    def __str__(self):
        """string representing the particles"""
        return " %8d %2d %4d %4d %4d %4d %+13.7e %+13.7e %+13.7e %14.8e %14.8e %10.4e %10.4e" \
            % (self.pid, 
               self.status,
               self.mother1.event_id+1 if self.mother1 else 0,
               self.mother2.event_id+1 if self.mother2 else 0,
               self.color1,
               self.color2,
               self.px,
               self.py,
               self.pz,
               self.E, 
               self.mass,
               self.vtim,
               self.helicity)
            
    def __eq__(self, other):
        
        if self.pid == other.pid and \
           self.status == other.status and \
           self.mother1 == other.mother1 and \
           self.mother2 == other.mother2 and \
           self.color1 == other.color1 and \
           self.color2 == other.color2 and \
           self.px == other.px and \
           self.py == other.py and \
           self.pz == other.pz and \
           self.E == other.E and \
           self.mass == other.mass and \
           self.vtim == other.vtim and \
           self.helicity == other.helicity:
            return True
        return False
        
        
        
            
    def __repr__(self):
        return 'Particle("%s", event=%s)' % (str(self), self.event)
        
class EventFile(file):
    """ """
    
    def __init__(self, path, mode='r', *args, **opt):
        """open file and read the banner [if in read mode]"""
        
        file.__init__(self, path, mode, *args, **opt)
        self.banner = ''
        if mode == 'r':
            line = ''
#            while '</init>' not in line.lower():
            while '</init>' not in line: ##remove lower
                try:
                    line  = file.next(self)
                except StopIteration:
                    self.seek(0)
                    self.banner = ''
                    break 
#                if "<event>" in line.lower():
#                if "<event" in line.lower():   ##for nlo
                if "<event" in line:   ##for nlo remove lower
                    self.seek(0)
                    self.banner = ''
                    break                     

                self.banner += line

    def get_banner(self):
        """return a banner object"""
        import madgraph.various.banner as banner
        output = banner.Banner()
        output.read_banner(self.banner.split('\n'))
        return output
    
    
    def next(self):
        """get next event"""
        text = ''
        line = ''
        mode = 0
        while '</event>' not in line:
 #           line = file.next(self).lower()
            line = file.next(self)#remove lower
            #if '<event>' in line:
            if '<event' in line: #for nlo
                mode = 1
            if mode:
                text += line
        return Event(text)
        
           
class Event(list):
    """Class storing a single event information (list of particles + global information)"""

    warning_order = True # raise a warning if the order of the particle are not in accordance of child/mother

    def __init__(self, text=None):
        """The initialization of an empty Event (or one associate to a text file)"""
        list.__init__(self)
        
        # First line information
        self.eventbox = "<event>"
        self.eventbox_end = "</event>"
        self.nexternal = 0
        self.ievent = 0
        self.wgt = 0
        self.aqcd = 0 
        self.scale = 0
        self.aqed = 0
        self.aqcd = 0
        # Weight information
        self.tag = ''
        self.comment = ''
        self.reweight_data ={}
        
        if text:
            self.parse(text)
            
    def parse(self, text):
        """Take the input file and create the structured information"""
#        text = re.sub(r'</?event', '', text) # remove pointless tag
       # text = re.sub(r'</?event>', '', text) # remove pointless tag
       # print "text="+str(text)
        status = 'first' 
        for line in text.split('\n'):
       #     line = line.strip()
           # print "line="+str(line)
            if '<event' in line :
              #  print "if <event in this line = "+str(line)
                self.eventbox=line
                continue
            if '</event' in line :
              #  print "if <\/event in this line = "+str(line)
                self.eventbox_end=line
                continue
            if not line: 
                continue
            if line.startswith('#'):
                self.comment += '%s\n' % line
                continue
            if 'first' == status:
                self.assign_scale_line(line)
                status = 'part' 
                continue
            
            if '<' in line:
                status = 'tag'
                
            if 'part' == status:
                self.append(Particle(line, event=self))
            else:
                self.tag += '%s\n' % line

        # assign the mother:
        for i,particle in enumerate(self):
            if self.warning_order:
                if i < particle.mother1 or i < particle.mother2:
                    logger.warning("Order of particle in the event did not agree with parent/child order. This might be problematic for some code.")
                    Event.warning_order = False
                                   
            if particle.mother1:
                particle.mother1 = self[int(particle.mother1) -1]
            if particle.mother2:
                particle.mother2 = self[int(particle.mother2) -1]

   
    def parse_reweight(self):
        """Parse the re-weight information in order to return a dictionary
           {key: value}. If no group is define group should be '' """
           
        self.reweight_data = {}
        self.reweight_order = []
        start, stop = self.tag.find('<rwgt>'), self.tag.find('</rwgt>')
        if start != -1 != stop :
            pattern = re.compile(r'''<\s*wgt id=(?:\'|\")(?P<id>[^\'\"]+)(?:\'|\")\s*>\s*(?P<val>[\ded+-.]*)\s*</wgt>''')
            data = pattern.findall(self.tag)
            try:
                self.reweight_data = dict([(pid, float(value)) for (pid, value) in data
                                           if not self.reweight_order.append(pid)])
                             # the if is to create the order file on the flight
            except ValueError, error:
                raise Exception, 'Event File has unvalid weight. %s' % error
            self.tag = self.tag[:start] + self.tag[stop+7:]
    
    def check(self):
        """check various property of the events"""
        
        #1. Check that the 4-momenta are conserved
        E, px, py, pz = 0,0,0,0
        absE, abspx, abspy, abspz = 0,0,0,0
        for particle in self:
            coeff = 1
            if particle.status == -1:
                coeff = -1
            elif particle.status != 1:
                continue
            E += coeff * particle.E
            absE += abs(particle.E)
            px += coeff * particle.px
            py += coeff * particle.py
            pz += coeff * particle.pz
            abspx += abs(particle.px)
            abspy += abs(particle.py)
            abspz += abs(particle.pz)
        # check that relative error is under control
        threshold = 5e-11
        if E/absE > threshold:
            logger.critical(self)
            raise Exception, "Do not conserve Energy %s, %s" % (E/absE, E)
        if px/abspx > threshold:
            logger.critical(self)
            raise Exception, "Do not conserve Px %s, %s" % (px/abspx, px)         
        if py/abspy > threshold:
            logger.critical(self)
            raise Exception, "Do not conserve Py %s, %s" % (py/abspy, py)
        if pz/abspz > threshold:
            logger.critical(self)
            raise Exception, "Do not conserve Pz %s, %s" % (pz/abspz, pz)
            
        #2. check the color of the event
        self.check_color_structure()
            
            
            
            
            
            
            
            
        

        

        

        
        
        
        
           
           
           
           
            
    def assign_scale_line(self, line):
        """read the line corresponding to global event line
        format of the line is:
        Nexternal IEVENT WEIGHT SCALE AEW AS
        """
        inputs = line.split()
       # print "intputs="+str(inputs)
       # print "input len = "+str(len(inputs))
        assert len(inputs) == 6
        self.nexternal=int(inputs[0])
        self.ievent=int(inputs[1])
        self.wgt=float(inputs[2])
        self.scale=float(inputs[3])
        self.aqed=float(inputs[4])
        self.aqcd=float(inputs[5])
        
    def get_tag_and_order(self):
        """Return the unique tag identifying the SubProcesses for the generation.
        Usefull for program like MadSpin and Reweight module."""
        
        initial, final, order = [], [], [[], []]
        for particle in self:
            if particle.status == -1:
                initial.append(particle.pid)
                order[0].append(particle.pid)
            elif particle.status == 1: 
                final.append(particle.pid)
                order[1].append(particle.pid)
        initial.sort(), final.sort()
        tag = (tuple(initial), tuple(final))
        return tag, order
    
    def check_color_structure(self):
        """check the validity of the color structure"""
        
        #1. check that each color is raised only once.
        color_index = collections.defaultdict(int)
        for particle in self:
            if particle.status in [-1,1]:
                if particle.color1:
                    color_index[particle.color1] +=1
                if particle.color2:
                    color_index[particle.color2] +=1     
                
        for key,value in color_index.items():
            if value > 2:
                print self
                print key, value
                raise Exception, 'Wrong color_flow'           
        
        #2. check that each parent present have coherent color-structure
        check = []
        popup_index = [] #check that the popup index are created in a unique way
        for particle in self:
            mothers = []
            childs = []
            if particle.mother1:
                mothers.append(particle.mother1)
            if particle.mother2 and particle.mother2 is not particle.mother1:
                mothers.append(particle.mother2)                 
            if not mothers:
                continue
            if (particle.mother1.event_id, particle.mother2.event_id) in check:
                continue
            check.append((particle.mother1.event_id, particle.mother2.event_id))
            
            childs = [p for p in self if p.mother1 is particle.mother1 and \
                                         p.mother2 is particle.mother2]
            
            mcolors = []
            manticolors = []
            for m in mothers:
                if m.color1:
                    if m.color1 in manticolors:
                        manticolors.remove(m.color1)
                    else:
                        mcolors.append(m.color1)
                if m.color2:
                    if m.color2 in mcolors:
                        mcolors.remove(m.color2)
                    else:
                        manticolors.append(m.color2)
            ccolors = []
            canticolors = []
            for m in childs:
                if m.color1:
                    if m.color1 in canticolors:
                        canticolors.remove(m.color1)
                    else:
                        ccolors.append(m.color1)
                if m.color2:
                    if m.color2 in ccolors:
                        ccolors.remove(m.color2)
                    else:
                        canticolors.append(m.color2)
            for index in mcolors[:]:
                if index in ccolors:
                    mcolors.remove(index)
                    ccolors.remove(index)
            for index in manticolors[:]:
                if index in canticolors:
                    manticolors.remove(index)
                    canticolors.remove(index)             
                        
            if mcolors != []:
                #only case is a epsilon_ijk structure.
                if len(canticolors) + len(mcolors) != 3:
                    logger.critical(str(self))
                    raise Exception, "Wrong color flow for %s -> %s" ([m.pid for m in mothers], [c.pid for c in childs])              
                else:
                    popup_index += canticolors
            elif manticolors != []:
                #only case is a epsilon_ijk structure.
                if len(ccolors) + len(manticolors) != 3:
                    logger.critical(str(self))
                    raise Exception, "Wrong color flow for %s -> %s" ([m.pid for m in mothers], [c.pid for c in childs])              
                else:
                    popup_index += ccolors

            # Check that color popup (from epsilon_ijk) are raised only once
            if len(popup_index) != len(set(popup_index)):
                logger.critical(self)
                raise Exception, "Wrong color flow: identical poping-up index, %s" % (popup_index)
            
            
            
            
    
        
    def __str__(self):
        """return a correctly formatted LHE event"""
                
#        out="""<event>
        out="""
%(eventbox)s
%(scale)s
%(particles)s
%(comments)s
%(tag)s
%(reweight)s
%(eventbox_end)s
""" 

        scale_str = "%2d %6d %+13.7e %14.8e %14.8e %14.8e" % \
            (self.nexternal,self.ievent,self.wgt,self.scale,self.aqed,self.aqcd)
        if self.reweight_data:
            # check that all key have an order if not add them at the end
            if set(self.reweight_data.keys()) != set(self.reweight_order):
                self.reweight_order += [k for k in self.reweight_data.keys() \
                                                if k not in self.reweight_order]

            reweight_str = '<rwgt>\n%s\n</rwgt>' % '\n'.join(
                        '<wgt id=\'%s\'> %+13.7e </wgt>' % (i, float(self.reweight_data[i]))
                        for i in self.reweight_order)
        else:
            reweight_str = '' 
        out = out % { 'eventbox': self.eventbox,
                      'scale': scale_str, 
                      'particles': '\n'.join([str(p) for p in self]),
                      'tag': self.tag,
                      'comments': self.comment,
                      'reweight': reweight_str,
                      'eventbox_end': self.eventbox_end}
        return re.sub('[\n]+', '\n', out)
    
    def get_momenta_str(self, get_order, allow_reversed=True):
        """return the momenta str in the order asked for"""
        
        
        #avoid to modify the input
        order = [list(get_order[0]), list(get_order[1])] 
        out = [''] *(len(order[0])+len(order[1]))
        for i, part in enumerate(self):
            if part.status == 1: #final
                try:
                    ind = order[1].index(part.pid)
                except ValueError, error:
                    if not allow_reversed:
                        raise error
                    else:
                        order = [[-i for i in get_order[0]],[-i for i in get_order[1]]]
                        try:
                            return self.get_momenta_str(order, False)
                        except ValueError:
                            raise error     
                position = len(order[0]) + ind
                order[1][ind] = 0   
            elif part.status == -1:
                try:
                    ind = order[0].index(part.pid)
                except ValueError, error:
                    if not allow_reversed:
                        raise error
                    else:
                        order = [[-i for i in get_order[0]],[-i for i in get_order[1]]]
                        try:
                            return self.get_momenta_str(order, False)
                        except ValueError:
                            raise error
                 
                position =  ind
                order[0][ind] = 0
            else: #intermediate
                continue
            out[position] = '%g %g %g %g \n'% (part.E, part.px, part.py, part.pz)
            
        out = ''.join(out).replace('e','d')
        return out    



if '__main__' == __name__:    


    import math
#####
#This script is to add virtual gammas in DY process because offshell gammas are not stored in event records in MG5.
#Before using it, please set bwcutoff very large to make Z boson always being onshell.
#(|M-M_onshellmass| <   (bwcutoff*decaywidth)*M     => then MG considers it as an onshell particle.) 
#
#This script is
#(1)Find lepton pair with the same flavour & opposite sign
#(2)Check if their mother is not Z boson
#(3)If not Z, define gamma*
#(4) Momentum of gamma* = sum[Momentum of l+,l-]
#(5) remove l+l- in event records
#(6) add gamma* / l+/l- in this order.
    ##### Load lhe file to modify#####
#    lhe = EventFile('unweighted_events.lhe')
    #lhefile='unweighted_events.lhe'
    lhefile='cmsgrid_final.lhe'
    #lhefile='cmsgrid_final_dy012j_nlo.lhe'
    #lhefile='cmsgrid_final_dy01234j_lo.lhe'
    lhe = EventFile(lhefile)
    output = open(lhefile+'_add_virtual_gamma.lhe', 'w')
    #write the banner to the output file
    output.write(lhe.banner)
    # Loop over all events
#len(lhe)
    for event in lhe:
##For an event in lhe file
 ##### declare lepton + - for DY process ######

        #check event info
       # print "nexternal="+str(event.nexternal)
       # print "ievent="+str(event.ievent)
       # print "wgt="+str(event.wgt)
       # print "aqcd="+str(event.aqcd)
       # print "scale="+str(event.scale)
       # print "aqed="+str(event.aqed)
       # print "aqcd="+str(event.aqcd)
       # print "tag="+str(event.tag)
       # print "comment="+str(event.comment)




###end of check event info
        lp = None
        lm = None
        Nl=0      ##The number of leptons##
        gamma_event=False


        ##### define e/mu/tau####                                                                                                                
        for particle in event:
            ##print str(particle)
            if particle.pid == 11 or particle.pid == 13 or particle.pid == 15:
                lp = particle
                Nl=Nl+1
            elif particle.pid == -11 or particle.pid == -13 or particle.pid == -15:
                lm = particle
                Nl=Nl+1
#        event.nexternal=Nptl

        ####If N_leptons ==2, => check if it is a gamma* event, which means no intermediate boson in event records###
        if Nl == 2:
            ###Check the lepton pair is the same flavour, has the same mothers (but not Z boson) => gamma* event
            if lm.pid == -lp.pid and lm.mother1 == lp.mother1 and lm.mother2 == lp.mother2 and lp.mother1.pid != 23 and lm.mother2.pid != 23:
                gamma_event=True
       ##declare gamma*##
        gamma_virtual= Particle(None,event)
        #######if gamma* event#######
        if gamma_event:
            ###remove l+l- in event record##
            event.remove(lp)
            event.remove(lm)
            ###define gamma*#### 
            gamma_virtual.event = event
            gamma_virtual.event_id=len(event)##ordering index
            gamma_virtual.pid= 22##gamma
            gamma_virtual.status= 2
            gamma_virtual.mother1=lm.mother1 ##set its mother to mother of l+l-
            gamma_virtual.mother2=lm.mother2
            gamma_virtual.color1 = 0
            gamma_virtual.color2 = 0
            gamma_virtual.px = lm.px+lp.px
            gamma_virtual.py = lm.py+lp.py
            gamma_virtual.pz = lm.pz+lp.pz
            gamma_virtual.E = lm.E+lp.E
            gamma_virtual.mass = math.sqrt(math.pow(gamma_virtual.E,2)-math.pow(gamma_virtual.px,2)-math.pow(gamma_virtual.py,2)-math.pow(gamma_virtual.pz,2))
            gamma_virtual.vtim = 0
            gamma_virtual.comment=''

            gamma_virtual.helicity = 0 ##? 

            event.append(gamma_virtual)

            lm.event_id=len(event)
            event.append(lm)
            lp.event_id=len(event)
            event.append(lp)
            ####set l+l-'s mother to gamma*####
            lp.mother1=gamma_virtual
            lp.mother2=gamma_virtual

            lm.mother1=gamma_virtual
            lm.mother2=gamma_virtual
     ###increase Nptl to Nptl+1 due to the new virtual gamma
            event.nexternal=event.nexternal+1


            event.parse
        output.write(str(event))
    output.write("</LesHouchesEvents>")
